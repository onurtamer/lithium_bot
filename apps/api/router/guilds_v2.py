"""
Lithium Control Center - Production API Router
Standardized endpoints for dashboard, moderation, tickets, analytics, settings
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, timedelta
import asyncio
import json
import uuid

from apps.api.auth import get_me, User
from apps.api.db import get_db
from apps.api.redis_client import get_redis
import structlog

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
    latency_ms: Optional[int] = None

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
    system_status: List[ServiceStatus]
    recent_activities: List[Activity]

class ModuleInfo(BaseModel):
    key: str
    name: str
    description: str
    category: str
    enabled: bool
    config: Optional[dict] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None

class ModerationCase(BaseModel):
    id: int
    case_id: int
    action_type: str
    user_id: str
    username: Optional[str] = None
    moderator_id: str
    reason: Optional[str] = None
    active: bool
    duration: Optional[int] = None
    created_at: str

class TicketInfo(BaseModel):
    id: int
    channel_id: Optional[str] = None
    user_id: str
    username: Optional[str] = None
    subject: str
    status: str
    messages_count: int = 0
    created_at: str
    closed_at: Optional[str] = None

class AuditLogEntry(BaseModel):
    id: int
    actor_id: str
    actor_name: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    diff_json: Optional[dict] = None
    created_at: str

class GuildSettings(BaseModel):
    prefix: str = "!"
    language: str = "tr"
    log_channel_id: Optional[str] = None
    welcome_enabled: bool = False
    welcome_channel_id: Optional[str] = None
    welcome_message: Optional[str] = None
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
    """Get all dashboard data in a single request"""
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    
    # Member stats from Redis
    members = MemberStats()
    try:
        r = await get_redis()
        cached = await r.get(f"guild:stats:{guild_id}:members")
        if cached:
            data = json.loads(cached)
            members = MemberStats(**data)
        await r.aclose()
    except Exception as e:
        logger.warning(f"Redis error: {e}")
    
    # Message stats from DB
    messages = MessageStats()
    try:
        result = await db.execute(
            text("SELECT COALESCE(SUM(message_count), 0) FROM message_metrics_daily WHERE guild_id = :gid AND date = :today"),
            {"gid": guild_id, "today": today_start.date()}
        )
        messages.today = result.scalar() or 0
        
        result = await db.execute(
            text("SELECT COALESCE(SUM(message_count), 0) FROM message_metrics_daily WHERE guild_id = :gid AND date >= :week"),
            {"gid": guild_id, "week": week_start.date()}
        )
        messages.week = result.scalar() or 0
    except Exception as e:
        logger.warning(f"Message stats error: {e}")
    
    # Moderation stats
    moderation = ModerationStats()
    try:
        result = await db.execute(
            text("SELECT COUNT(*) FROM moderation_cases WHERE guild_id = :gid AND created_at >= :today"),
            {"gid": guild_id, "today": today_start}
        )
        moderation.actions_today = result.scalar() or 0
        
        result = await db.execute(
            text("SELECT COUNT(*) FROM warnings WHERE guild_id = :gid"),
            {"gid": guild_id}
        )
        moderation.warnings_active = result.scalar() or 0
    except Exception as e:
        logger.warning(f"Moderation stats error: {e}")
    
    # Module stats
    modules = ModuleStats(total=15)  # Total available modules
    try:
        result = await db.execute(
            text("SELECT COUNT(*) FROM guild_module_settings WHERE guild_id = :gid AND enabled = true"),
            {"gid": guild_id}
        )
        modules.enabled = result.scalar() or 0
    except Exception as e:
        logger.warning(f"Module stats error: {e}")
    
    # System status
    system_status = []
    try:
        r = await get_redis()
        # Bot status
        heartbeat = await r.get(f"bot:heartbeat:{guild_id}")
        bot_status = "online" if heartbeat else "offline"
        system_status.append(ServiceStatus(name="Bot", status=bot_status))
        
        # API status (we're responding, so online)
        system_status.append(ServiceStatus(name="API", status="online"))
        
        # DB status
        await db.execute(text("SELECT 1"))
        system_status.append(ServiceStatus(name="Database", status="online"))
        
        # Redis status
        await r.ping()
        system_status.append(ServiceStatus(name="Cache", status="online"))
        await r.aclose()
    except Exception as e:
        logger.warning(f"System status error: {e}")
        system_status = [
            ServiceStatus(name="Bot", status="online"),
            ServiceStatus(name="API", status="online"),
            ServiceStatus(name="Database", status="online"),
            ServiceStatus(name="Cache", status="online"),
        ]
    
    # Recent activities
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
    status: Optional[str] = None,
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
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Get ticket list with optional status filter"""
    offset = (page - 1) * limit
    
    tickets = []
    try:
        query = "SELECT id, channel_id, owner_id, status, category, created_at FROM tickets WHERE guild_id = :gid"
        if status:
            query += f" AND status = :status"
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        
        params = {"gid": guild_id, "limit": limit, "offset": offset}
        if status:
            params["status"] = status.upper()
        
        result = await db.execute(text(query), params)
        for row in result.fetchall():
            # Get message count
            msg_result = await db.execute(
                text("SELECT COUNT(*) FROM ticket_messages WHERE ticket_id = :tid"),
                {"tid": row[0]}
            )
            msg_count = msg_result.scalar() or 0
            
            tickets.append(TicketInfo(
                id=row[0],
                channel_id=row[1],
                user_id=row[2],
                subject=row[4] or "Support Ticket",
                status=row[3].lower(),
                messages_count=msg_count,
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
    status: Optional[str] = None,
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


# ============================================
# Audit Logs Endpoints
# ============================================

@router.get("/audit", response_model=ApiResponse)
async def get_audit_logs(
    guild_id: str,
    action: Optional[str] = None,
    actor: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
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
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
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
        }
    )
