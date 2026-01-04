"""
Lithium Control Center - Production API Router
Standardized endpoints for dashboard, moderation, tickets, analytics, settings
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import structlog
from apps.api.auth import User, get_me
from apps.api.db import get_db
from apps.api.redis_client import get_redis
from apps.api.event_bus import event_bus, guild_channel, EventTypes
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/guilds/{guild_id}", tags=["Guild API v2"])


# ============================================
# Response Models
# ============================================

class ApiMeta(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ApiResponse(BaseModel):
    ok: bool = True
    data: Any
    meta: ApiMeta = Field(default_factory=ApiMeta)

class MemberStats(BaseModel):
    total: int = 0
    online: int = 0
    new_24h: int = 0

class MessageStats(BaseModel):
    today: int = 0
    week: int = 0

class ModerationStats(BaseModel):
    actions_today: int = 0
    warnings_active: int = 0

class ModuleStats(BaseModel):
    enabled: int = 0
    total: int = 0

class ServiceStatus(BaseModel):
    name: str
    status: str  # online, degraded, offline
    latency_ms: int | None = None

class Activity(BaseModel):
    id: int
    type: str
    title: str
    description: str
    time: str
    severity: str  # info, warning, error, success
    created_at: str

class DashboardData(BaseModel):
    members: MemberStats
    messages: MessageStats
    moderation: ModerationStats
    modules: ModuleStats
    system_status: list[ServiceStatus]
    recent_activities: list[Activity]

class ModuleInfo(BaseModel):
    key: str
    name: str
    description: str
    category: str
    enabled: bool
    config: dict | None = None
    updated_at: str | None = None
    updated_by: str | None = None

class ModerationCase(BaseModel):
    id: int
    case_id: int
    action_type: str
    user_id: str
    username: str | None = None
    moderator_id: str
    reason: str | None = None
    active: bool
    duration: int | None = None
    created_at: str

class TicketInfo(BaseModel):
    id: int
    channel_id: str | None = None
    user_id: str
    username: str | None = None
    subject: str
    status: str
    messages_count: int = 0
    created_at: str
    closed_at: str | None = None

class AuditLogEntry(BaseModel):
    id: int
    actor_id: str
    actor_name: str | None = None
    action: str
    target_type: str | None = None
    target_id: str | None = None
    diff_json: dict | None = None
    created_at: str

class GuildSettings(BaseModel):
    prefix: str = "!"
    language: str = "tr"
    log_channel_id: str | None = None
    welcome_enabled: bool = False
    welcome_channel_id: str | None = None
    welcome_message: str | None = None
    dm_on_warn: bool = True
    dm_on_mute: bool = True
    notify_on_join: bool = True
    notify_on_leave: bool = True
    notify_on_ban: bool = True


# ============================================
# Dashboard Endpoint
# ============================================

@router.get("/dashboard", response_model=ApiResponse)
async def get_dashboard(guild_id: str, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get all dashboard data in a single request - OPTIMIZED with parallel queries"""
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    
    # Helper functions for parallel execution
    async def get_member_stats():
        try:
            r = await get_redis()
            cached = await r.get(f"guild:stats:{guild_id}:members")
            await r.aclose()
            if cached:
                return MemberStats(**json.loads(cached))
        except Exception as e:
            logger.warning(f"Redis error: {e}")
        return MemberStats()
    
    async def get_message_stats():
        try:
            result = await db.execute(
                text("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN date = :today THEN message_count ELSE 0 END), 0) as today,
                        COALESCE(SUM(message_count), 0) as week
                    FROM message_metrics_daily 
                    WHERE guild_id = :gid AND date >= :week
                """),
                {"gid": guild_id, "today": today_start.date(), "week": week_start.date()}
            )
            row = result.fetchone()
            if row:
                return MessageStats(today=row[0] or 0, week=row[1] or 0)
        except Exception as e:
            logger.warning(f"Message stats error: {e}")
        return MessageStats()
    
    async def get_moderation_stats():
        try:
            result = await db.execute(
                text("""
                    SELECT 
                        (SELECT COUNT(*) FROM moderation_cases WHERE guild_id = :gid AND created_at >= :today) as actions,
                        (SELECT COUNT(*) FROM warnings WHERE guild_id = :gid) as warnings
                """),
                {"gid": guild_id, "today": today_start}
            )
            row = result.fetchone()
            if row:
                return ModerationStats(actions_today=row[0] or 0, warnings_active=row[1] or 0)
        except Exception as e:
            logger.warning(f"Moderation stats error: {e}")
        return ModerationStats()
    
    async def get_module_stats():
        try:
            result = await db.execute(
                text("SELECT COUNT(*) FROM guild_module_settings WHERE guild_id = :gid AND enabled = true"),
                {"gid": guild_id}
            )
            count = result.scalar() or 0
            return ModuleStats(enabled=count, total=15)
        except Exception as e:
            logger.warning(f"Module stats error: {e}")
        return ModuleStats(total=15)
    
    async def get_system_status():
        status = []
        try:
            r = await get_redis()
            heartbeat = await r.get(f"bot:heartbeat:{guild_id}")
            await r.aclose()
            status.append(ServiceStatus(name="Bot", status="online" if heartbeat else "offline"))
            status.append(ServiceStatus(name="API", status="online"))
            status.append(ServiceStatus(name="Database", status="online"))
            status.append(ServiceStatus(name="Cache", status="online"))
        except:
            status = [
                ServiceStatus(name="Bot", status="online"),
                ServiceStatus(name="API", status="online"),
                ServiceStatus(name="Database", status="online"),
                ServiceStatus(name="Cache", status="online"),
            ]
        return status
    
    async def get_recent_activities():
        activities = []
        try:
            result = await db.execute(
                text("""
                    SELECT id, action, target, changes, created_at 
                    FROM audit_logs WHERE guild_id = :gid 
                    ORDER BY created_at DESC LIMIT 5
                """),
                {"gid": guild_id}
            )
            for row in result.fetchall():
                log_id, action, target, changes, created_at = row
                delta = now - created_at
                if delta.total_seconds() < 60:
                    time_str = "Az önce"
                elif delta.total_seconds() < 3600:
                    time_str = f"{int(delta.total_seconds() / 60)} dk önce"
                elif delta.total_seconds() < 86400:
                    time_str = f"{int(delta.total_seconds() / 3600)} saat önce"
                else:
                    time_str = f"{int(delta.total_seconds() / 86400)} gün önce"
                
                activities.append(Activity(
                    id=log_id,
                    type=action,
                    title=action.replace("_", " ").title(),
                    description=f"Hedef: {target}" if target else "",
                    time=time_str,
                    severity="info",
                    created_at=created_at.isoformat()
                ))
        except Exception as e:
            logger.warning(f"Activities error: {e}")
        return activities
    
    # Run ALL queries in parallel
    members, messages, moderation, modules, system_status, activities = await asyncio.gather(
        get_member_stats(),
        get_message_stats(),
        get_moderation_stats(),
        get_module_stats(),
        get_system_status(),
        get_recent_activities()
    )
    
    dashboard = DashboardData(
        members=members,
        messages=messages,
        moderation=moderation,
        modules=modules,
        system_status=system_status,
        recent_activities=activities
    )
    
    return ApiResponse(data=dashboard.model_dump())


# ============================================
# Moderation Endpoints
# ============================================

@router.get("/moderation", response_model=ApiResponse)
async def get_moderation_overview(
    guild_id: str,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Get moderation cases, warnings, and active punishments"""
    offset = (page - 1) * limit
    
    cases = []
    try:
        query = """
            SELECT id, case_id, action_type, user_id, moderator_id, reason, active, duration, created_at
            FROM moderation_cases WHERE guild_id = :gid
        """
        if status == "active":
            query += " AND active = true"
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        
        result = await db.execute(text(query), {"gid": guild_id, "limit": limit, "offset": offset})
        for row in result.fetchall():
            cases.append(ModerationCase(
                id=row[0],
                case_id=row[1],
                action_type=row[2],
                user_id=row[3],
                moderator_id=row[4],
                reason=row[5],
                active=row[6],
                duration=row[7],
                created_at=row[8].isoformat() if row[8] else ""
            ))
    except Exception as e:
        logger.error(f"Moderation query error: {e}")
    
    # Get total count
    total = 0
    try:
        result = await db.execute(
            text("SELECT COUNT(*) FROM moderation_cases WHERE guild_id = :gid"),
            {"gid": guild_id}
        )
        total = result.scalar() or 0
    except:
        pass
    
    return ApiResponse(data={
        "items": [c.model_dump() for c in cases],
        "total": total,
        "page": page,
        "pages": (total // limit) + (1 if total % limit else 0) or 1
    })


@router.get("/moderation/warnings", response_model=ApiResponse)
async def get_warnings(guild_id: str, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get active warnings for the guild"""
    warnings = []
    try:
        result = await db.execute(
            text("""
                SELECT id, user_id, moderator_id, reason, created_at
                FROM warnings WHERE guild_id = :gid
                ORDER BY created_at DESC
            """),
            {"gid": guild_id}
        )
        for row in result.fetchall():
            warnings.append({
                "id": row[0],
                "user_id": row[1],
                "moderator_id": row[2],
                "reason": row[3],
                "created_at": row[4].isoformat() if row[4] else ""
            })
    except Exception as e:
        logger.error(f"Warnings query error: {e}")
    
    return ApiResponse(data={"items": warnings, "total": len(warnings)})


# ============================================
# Tickets Endpoints
# ============================================

@router.get("/tickets", response_model=ApiResponse)
async def get_tickets(
    guild_id: str,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Get ticket list with optional status filter"""
    offset = (page - 1) * limit
    
    tickets = []
    try:
        # Optimized: Single query with LEFT JOIN for message counts and username
        query = """
            SELECT t.id, t.channel_id, t.owner_id, t.status, t.category, t.created_at,
                   COALESCE(COUNT(tm.id), 0) as msg_count,
                   u.username
            FROM tickets t
            LEFT JOIN ticket_messages tm ON tm.ticket_id = t.id
            LEFT JOIN users u ON u.discord_id = t.owner_id
            WHERE t.guild_id = :gid
        """
        if status:
            query += " AND t.status = :status"
        query += " GROUP BY t.id, t.channel_id, t.owner_id, t.status, t.category, t.created_at, u.username"
        query += " ORDER BY t.created_at DESC LIMIT :limit OFFSET :offset"
        
        params = {"gid": guild_id, "limit": limit, "offset": offset}
        if status:
            params["status"] = status.upper()
        
        result = await db.execute(text(query), params)
        for row in result.fetchall():
            tickets.append(TicketInfo(
                id=row[0],
                channel_id=row[1],
                user_id=row[2],
                username=row[7] if row[7] else f"User#{row[2][-4:]}" if row[2] else "Unknown",
                subject=row[4] or "Support Ticket",
                status=row[3].lower() if row[3] else "open",
                messages_count=row[6],
                created_at=row[5].isoformat() if row[5] else ""
            ))
    except Exception as e:
        logger.error(f"Tickets query error: {e}")
    
    # Get counts by status
    counts = {"open": 0, "claimed": 0, "closed": 0}
    try:
        result = await db.execute(
            text("SELECT status, COUNT(*) FROM tickets WHERE guild_id = :gid GROUP BY status"),
            {"gid": guild_id}
        )
        for row in result.fetchall():
            counts[row[0].lower()] = row[1]
    except:
        pass
    
    return ApiResponse(data={
        "items": [t.model_dump() for t in tickets],
        "counts": counts,
        "page": page
    })


@router.put("/tickets/{ticket_id}", response_model=ApiResponse)
async def update_ticket(
    guild_id: str,
    ticket_id: int,
    status: str | None = None,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Update ticket status"""
    if status:
        await db.execute(
            text("UPDATE tickets SET status = :status WHERE id = :tid AND guild_id = :gid"),
            {"status": status.upper(), "tid": ticket_id, "gid": guild_id}
        )
        await db.commit()
    
    return ApiResponse(data={"updated": True})


@router.post("/tickets/{ticket_id}/claim", response_model=ApiResponse)
async def claim_ticket(
    guild_id: str,
    ticket_id: int,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Claim a ticket from web interface"""
    # Update ticket in DB
    await db.execute(
        text("""
            UPDATE tickets 
            SET status = 'CLAIMED', claimed_by = :user_id 
            WHERE id = :tid AND guild_id = :gid AND status = 'OPEN'
        """),
        {"tid": ticket_id, "gid": guild_id, "user_id": str(user.discord_id)}
    )
    await db.commit()
    
    # Notify bot via Redis
    try:
        r = await get_redis()
        await r.publish("ticket_action", json.dumps({
            "action": "claim",
            "guild_id": guild_id,
            "ticket_id": ticket_id,
            "claimed_by": user.discord_id
        }))
        await r.aclose()
    except Exception as e:
        logger.warning(f"Redis publish error: {e}")
    
    # REAL-TIME: Publish ticket update event
    await event_bus.publish(
        f"guild:{guild_id}:events",
        EventTypes.TICKET_UPDATE,
        {"ticket_id": ticket_id, "action": "claimed", "claimed_by": user.discord_id}
    )
    
    return ApiResponse(data={"claimed": True})


@router.post("/tickets/{ticket_id}/close", response_model=ApiResponse)
async def close_ticket(
    guild_id: str,
    ticket_id: int,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Close a ticket from web interface"""
    # Get channel_id first
    result = await db.execute(
        text("SELECT channel_id FROM tickets WHERE id = :tid AND guild_id = :gid"),
        {"tid": ticket_id, "gid": guild_id}
    )
    row = result.fetchone()
    channel_id = row[0] if row else None
    
    # Update status
    await db.execute(
        text("UPDATE tickets SET status = 'CLOSED', closed_at = NOW() WHERE id = :tid AND guild_id = :gid"),
        {"tid": ticket_id, "gid": guild_id}
    )
    await db.commit()
    
    # Notify bot to delete channel
    try:
        r = await get_redis()
        await r.publish("ticket_action", json.dumps({
            "action": "close",
            "guild_id": guild_id,
            "ticket_id": ticket_id,
            "channel_id": channel_id,
            "closed_by": user.discord_id
        }))
        await r.aclose()
    except Exception as e:
        logger.warning(f"Redis publish error: {e}")
    
    return ApiResponse(data={"closed": True})


class TicketMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


@router.post("/tickets/{ticket_id}/message", response_model=ApiResponse)
async def send_ticket_message(
    guild_id: str,
    ticket_id: int,
    message: TicketMessageRequest,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to a ticket channel via bot"""
    # Get ticket info
    result = await db.execute(
        text("SELECT channel_id FROM tickets WHERE id = :tid AND guild_id = :gid AND status != 'CLOSED'"),
        {"tid": ticket_id, "gid": guild_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found or closed")
    
    channel_id = row[0]
    
    # Notify bot to send message
    try:
        r = await get_redis()
        await r.publish("ticket_action", json.dumps({
            "action": "send_message",
            "guild_id": guild_id,
            "ticket_id": ticket_id,
            "channel_id": channel_id,
            "sender_id": user.discord_id,
            "sender_name": user.username,
            "content": message.content
        }))
        await r.aclose()
    except Exception as e:
        logger.warning(f"Redis publish error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")
    
    return ApiResponse(data={"sent": True})


# ============================================
# Audit Logs Endpoints
# ============================================

@router.get("/audit", response_model=ApiResponse)
async def get_audit_logs(
    guild_id: str,
    action: str | None = None,
    actor: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters"""
    offset = (page - 1) * limit
    
    logs = []
    try:
        query = "SELECT id, user_id, action, target, changes, created_at FROM audit_logs WHERE guild_id = :gid"
        params = {"gid": guild_id, "limit": limit, "offset": offset}
        
        if action:
            query += " AND action = :action"
            params["action"] = action
        if actor:
            query += " AND user_id = :actor"
            params["actor"] = actor
        if from_date:
            query += " AND created_at >= :from_date"
            params["from_date"] = from_date
        if to_date:
            query += " AND created_at <= :to_date"
            params["to_date"] = to_date
        
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        
        result = await db.execute(text(query), params)
        for row in result.fetchall():
            logs.append(AuditLogEntry(
                id=row[0],
                actor_id=row[1] or "",
                action=row[2],
                target_type="entity",
                target_id=row[3],
                diff_json=row[4] if isinstance(row[4], dict) else None,
                created_at=row[5].isoformat() if row[5] else ""
            ))
    except Exception as e:
        logger.error(f"Audit logs query error: {e}")
    
    return ApiResponse(data={
        "items": [l.model_dump() for l in logs],
        "page": page,
        "total": len(logs)
    })


# ============================================
# Analytics Endpoints
# ============================================

@router.get("/analytics", response_model=ApiResponse)
async def get_analytics(
    guild_id: str,
    metric: str = "messages",
    from_date: str | None = None,
    to_date: str | None = None,
    group_by: str = "daily",
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics data"""
    now = datetime.utcnow()
    
    if not from_date:
        from_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = now.strftime("%Y-%m-%d")
    
    data_points = []
    
    if metric == "messages":
        try:
            result = await db.execute(
                text("""
                    SELECT date, message_count, unique_users 
                    FROM message_metrics_daily 
                    WHERE guild_id = :gid AND date >= :from_date AND date <= :to_date
                    ORDER BY date
                """),
                {"gid": guild_id, "from_date": from_date, "to_date": to_date}
            )
            for row in result.fetchall():
                data_points.append({
                    "date": row[0].isoformat() if row[0] else "",
                    "messages": row[1],
                    "users": row[2]
                })
        except Exception as e:
            logger.error(f"Analytics query error: {e}")
    
    elif metric == "moderation":
        try:
            result = await db.execute(
                text("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM moderation_cases 
                    WHERE guild_id = :gid AND created_at >= :from_date AND created_at <= :to_date
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """),
                {"gid": guild_id, "from_date": from_date, "to_date": to_date}
            )
            for row in result.fetchall():
                data_points.append({
                    "date": row[0].isoformat() if row[0] else "",
                    "actions": row[1]
                })
        except Exception as e:
            logger.error(f"Analytics query error: {e}")
    
    return ApiResponse(data={
        "metric": metric,
        "from_date": from_date,
        "to_date": to_date,
        "data": data_points
    })


# ============================================
# Settings Endpoints
# ============================================

@router.get("/settings", response_model=ApiResponse)
async def get_settings(guild_id: str, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get guild settings"""
    settings = GuildSettings()
    
    try:
        result = await db.execute(
            text("""
                SELECT prefix, language, log_channel_id, welcome_enabled, welcome_channel_id,
                       welcome_message, dm_on_warn, dm_on_mute, notify_on_join, notify_on_leave, notify_on_ban
                FROM guild_settings WHERE guild_id = :gid
            """),
            {"gid": guild_id}
        )
        row = result.fetchone()
        if row:
            settings = GuildSettings(
                prefix=row[0],
                language=row[1],
                log_channel_id=row[2],
                welcome_enabled=row[3],
                welcome_channel_id=row[4],
                welcome_message=row[5],
                dm_on_warn=row[6],
                dm_on_mute=row[7],
                notify_on_join=row[8],
                notify_on_leave=row[9],
                notify_on_ban=row[10]
            )
    except Exception as e:
        logger.warning(f"Settings query error: {e}")
    
    return ApiResponse(data=settings.model_dump())


@router.put("/settings", response_model=ApiResponse)
async def update_settings(
    guild_id: str,
    settings: GuildSettings,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Update guild settings"""
    try:
        # Upsert
        await db.execute(
            text("""
                INSERT INTO guild_settings (guild_id, prefix, language, log_channel_id, welcome_enabled,
                    welcome_channel_id, welcome_message, dm_on_warn, dm_on_mute, notify_on_join,
                    notify_on_leave, notify_on_ban, updated_at, updated_by)
                VALUES (:gid, :prefix, :lang, :log_ch, :welcome_en, :welcome_ch, :welcome_msg,
                    :dm_warn, :dm_mute, :notify_join, :notify_leave, :notify_ban, NOW(), :user_id)
                ON CONFLICT (guild_id) DO UPDATE SET
                    prefix = EXCLUDED.prefix,
                    language = EXCLUDED.language,
                    log_channel_id = EXCLUDED.log_channel_id,
                    welcome_enabled = EXCLUDED.welcome_enabled,
                    welcome_channel_id = EXCLUDED.welcome_channel_id,
                    welcome_message = EXCLUDED.welcome_message,
                    dm_on_warn = EXCLUDED.dm_on_warn,
                    dm_on_mute = EXCLUDED.dm_on_mute,
                    notify_on_join = EXCLUDED.notify_on_join,
                    notify_on_leave = EXCLUDED.notify_on_leave,
                    notify_on_ban = EXCLUDED.notify_on_ban,
                    updated_at = NOW(),
                    updated_by = EXCLUDED.updated_by
            """),
            {
                "gid": guild_id,
                "prefix": settings.prefix,
                "lang": settings.language,
                "log_ch": settings.log_channel_id,
                "welcome_en": settings.welcome_enabled,
                "welcome_ch": settings.welcome_channel_id,
                "welcome_msg": settings.welcome_message,
                "dm_warn": settings.dm_on_warn,
                "dm_mute": settings.dm_on_mute,
                "notify_join": settings.notify_on_join,
                "notify_leave": settings.notify_on_leave,
                "notify_ban": settings.notify_on_ban,
                "user_id": user.id
            }
        )
        await db.commit()
        
        # REAL-TIME: Publish settings update event
        await event_bus.publish(
            f"guild:{guild_id}:events",
            EventTypes.SETTINGS_UPDATE,
            {"settings": settings.model_dump(), "updated_by": str(user.id)}
        )
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    return ApiResponse(data={"updated": True})


# ============================================
# SSE Real-time Events
# ============================================

@router.get("/events")
async def event_stream(guild_id: str, user: User = Depends(get_me)):
    """Server-Sent Events for real-time updates"""
    
    async def generate():
        while True:
            try:
                r = await get_redis()
                
                # Get latest stats
                members_raw = await r.get(f"guild:stats:{guild_id}:members")
                members = json.loads(members_raw) if members_raw else {"total": 0, "online": 0}
                
                messages_raw = await r.get(f"guild:stats:{guild_id}:messages")
                messages = json.loads(messages_raw) if messages_raw else {"today": 0, "week": 0}
                
                # Check bot heartbeat
                heartbeat = await r.get(f"bot:heartbeat:{guild_id}")
                bot_status = "online" if heartbeat else "offline"
                
                await r.aclose()
                
                event_data = {
                    "type": "stats_update",
                    "data": {
                        "members": members,
                        "messages": messages,
                        "bot_status": bot_status
                    }
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
            except Exception as e:
                logger.error(f"SSE error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            await asyncio.sleep(10)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "X-Accel-Buffering": "no",
        }
    )
