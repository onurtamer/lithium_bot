"""
Generic Module Configuration Router for Lithium Control Center
Provides CRUD operations for all module settings with versioning support.
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from lithium_core.database.session import get_db
from lithium_core.models import User, OAuthSession
from .auth import get_me
from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from datetime import datetime
import redis.asyncio as redis
import json
import os
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/guilds/{guild_id}", tags=["modules"])

# ============================================
# Pydantic Models
# ============================================

class ModuleStatus(BaseModel):
    module_key: str
    display_name: str
    description: str
    icon: str
    category: str
    enabled: bool
    risk_level: str
    has_draft: bool
    last_updated: Optional[str] = None

class ModuleConfig(BaseModel):
    module_key: str
    enabled: bool
    config: Dict[str, Any]
    last_updated: str
    updated_by: Optional[Dict[str, str]] = None
    version: int
    has_draft: bool
    draft_config: Optional[Dict[str, Any]] = None

class ModuleUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    publish: bool = True

class ModuleUpdateResponse(BaseModel):
    status: str
    version: int
    published: bool
    bot_notified: bool

class ModuleTestRequest(BaseModel):
    test_type: str  # message, user, event
    content: Optional[str] = None
    user_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None

class ModuleTestResponse(BaseModel):
    would_trigger: bool
    rules_matched: List[Dict[str, str]]
    preview_response: Optional[Dict[str, Any]] = None

class GuildMetrics(BaseModel):
    members: Dict[str, int]
    messages: Dict[str, int]
    moderation: Dict[str, int]
    leveling: Optional[Dict[str, int]] = None

# ============================================
# Module Definitions
# ============================================

MODULES = {
    "moderation_audit": {
        "display_name": "Denetim Kayıtları",
        "description": "Mesaj düzenleme/silme, ses kanalı hareketleri, üye değişiklikleri",
        "icon": "FileText",
        "category": "moderation",
        "risk_level": "low",
        "default_config": {"log_channel_id": None, "events": ["message_edit", "message_delete", "member_join", "member_leave"]}
    },
    "automod": {
        "display_name": "Otomatik Moderasyon",
        "description": "Küfür filtresi, link engelleyici, spam koruması",
        "icon": "Shield",
        "category": "moderation",
        "risk_level": "medium",
        "default_config": {
            "profanity": {"enabled": True, "customWords": [], "action": "delete"},
            "links": {"enabled": True, "whitelist": [], "action": "delete"},
            "caps": {"enabled": True, "threshold": 70, "minLength": 10, "action": "warn"},
            "spam": {"enabled": True, "messageThreshold": 5, "interval": 5, "action": "mute", "muteDuration": 300},
            "exemptRoles": [], "exemptChannels": []
        }
    },
    "jail": {
        "display_name": "Hapis Sistemi",
        "description": "Kural ihlali yapan kullanıcıları izole edin",
        "icon": "Lock",
        "category": "moderation",
        "risk_level": "high",
        "default_config": {
            "jailRoleId": None, "jailChannelId": None, "logChannelId": None,
            "autoJail": {"onRaidDetection": True, "onSpamThreshold": 5, "onWarningThreshold": 3},
            "jailMessage": "⛓️ **{user}** hapse atıldı!", "releaseMessage": "🔓 **{user}** serbest bırakıldı!"
        }
    },
    "temp_mute": {
        "display_name": "Süreli Susturma",
        "description": "Kullanıcıları belirli süre susturun",
        "icon": "VolumeX",
        "category": "moderation",
        "risk_level": "medium",
        "default_config": {"muteRoleId": None, "logChannelId": None, "defaultDuration": 600}
    },
    "anti_raid": {
        "display_name": "Raid Koruması",
        "description": "Toplu katılım ve bot saldırılarını engeller",
        "icon": "ShieldAlert",
        "category": "moderation",
        "risk_level": "high",
        "default_config": {"joinThreshold": 10, "joinInterval": 60, "action": "lockdown", "alertChannelId": None}
    },
    "tickets": {
        "display_name": "Ticket Sistemi",
        "description": "Destek talepleri için özel kanal yönetimi",
        "icon": "Ticket",
        "category": "utility",
        "risk_level": "low",
        "default_config": {"categoryId": None, "supportRoles": [], "welcomeMessage": "Merhaba! Size nasıl yardımcı olabiliriz?"}
    },
    "leveling": {
        "display_name": "Seviye Sistemi",
        "description": "XP kazanma ve seviye atlama sistemi",
        "icon": "TrendingUp",
        "category": "community",
        "risk_level": "low",
        "default_config": {
            "xpPerMessage": {"min": 15, "max": 25}, "xpCooldown": 60,
            "levelUpChannel": None, "levelUpMessage": "🎉 Tebrikler {user}! **Seviye {level}** oldun!",
            "rewards": [], "ignoredChannels": [], "ignoredRoles": [],
            "rankCard": {"backgroundColor": "#1a1a24", "accentColor": "#5865F2", "showAvatar": True}
        }
    },
    "economy": {
        "display_name": "Ekonomi",
        "description": "Sunucu içi para birimi ve ticaret",
        "icon": "Coins",
        "category": "community",
        "risk_level": "low",
        "default_config": {"currencyName": "Coin", "currencySymbol": "💰", "dailyAmount": 100, "workCooldown": 3600}
    },
    "starboard": {
        "display_name": "Starboard",
        "description": "En beğenilen mesajları özel kanalda sergileyin",
        "icon": "Star",
        "category": "community",
        "risk_level": "low",
        "default_config": {"channelId": None, "threshold": 3, "emoji": "⭐", "ignoredChannels": []}
    },
    "reaction_roles": {
        "display_name": "Tepki Rolleri",
        "description": "Kullanıcıların emoji ile rol almasını sağlayın",
        "icon": "Smile",
        "category": "utility",
        "risk_level": "medium",
        "default_config": {"maxMenusPerGuild": 10}
    },
    "giveaways": {
        "display_name": "Çekilişler",
        "description": "Kolay ve adil çekiliş sistemi",
        "icon": "Gift",
        "category": "community",
        "risk_level": "low",
        "default_config": {"defaultChannel": None, "maxWinners": 10, "requireRoles": False}
    },
    "birthdays": {
        "display_name": "Doğum Günleri",
        "description": "Üyelerin doğum günlerini kutlayın",
        "icon": "Cake",
        "category": "community",
        "risk_level": "low",
        "default_config": {"channelId": None, "roleId": None, "message": "🎂 Bugün {user} adlı üyemizin doğum günü!"}
    },
    "suggestions": {
        "display_name": "Öneri Sistemi",
        "description": "Kullanıcı önerilerini toplayın ve yönetin",
        "icon": "MessageSquarePlus",
        "category": "utility",
        "risk_level": "low",
        "default_config": {"channelId": None, "approvalRequired": False, "upvoteEmoji": "👍", "downvoteEmoji": "👎"}
    },
    "fun_games": {
        "display_name": "Eğlence & Oyunlar",
        "description": "Taş-kağıt-makas, 8ball, düellolar",
        "icon": "Gamepad2",
        "category": "fun",
        "risk_level": "low",
        "default_config": {"rpsEnabled": True, "coinflipEnabled": True, "8ballEnabled": True, "duelEnabled": True}
    },
    "utilities": {
        "display_name": "Yardımcı Araçlar",
        "description": "Çeviri, anket, hava durumu, finans",
        "icon": "Wrench",
        "category": "utility",
        "risk_level": "low",
        "default_config": {"translateEnabled": True, "pollEnabled": True, "weatherEnabled": True, "financeEnabled": True}
    },
}

# ============================================
# Helper Functions
# ============================================

async def get_redis() -> redis.Redis:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    return redis.from_url(redis_url)

async def notify_bot(guild_id: str, module_key: str, action: str = "update"):
    """Publish config change event to Redis for bot to pick up"""
    try:
        r = await get_redis()
        await r.publish("guild_config_changed", json.dumps({
            "guild_id": guild_id,
            "module": module_key,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }))
        await r.aclose()
        return True
    except Exception as e:
        logger.error(f"Failed to notify bot: {e}")
        return False

async def get_guild_module_config(db: AsyncSession, guild_id: str, module_key: str) -> dict:
    """Get module config from database or return default"""
    # Try to fetch from guild_module_settings table
    result = await db.execute(
        text("SELECT enabled, config_json, draft_json, version, updated_by, updated_at FROM guild_module_settings WHERE guild_id = :gid AND module_key = :mk"),
        {"gid": guild_id, "mk": module_key}
    )
    row = result.fetchone()
    
    if row:
        return {
            "enabled": row[0],
            "config": row[1] or MODULES[module_key]["default_config"],
            "draft_config": row[2],
            "version": row[3] or 1,
            "updated_by": row[4],
            "updated_at": row[5].isoformat() if row[5] else None
        }
    else:
        # Return default config
        return {
            "enabled": False,
            "config": MODULES[module_key]["default_config"],
            "draft_config": None,
            "version": 1,
            "updated_by": None,
            "updated_at": None
        }

async def save_guild_module_config(db: AsyncSession, guild_id: str, module_key: str, 
                                    enabled: bool, config: dict, user_id: str, 
                                    publish: bool = True) -> int:
    """Save module config to database"""
    now = datetime.utcnow()
    
    # Check if exists
    result = await db.execute(
        text("SELECT id, version FROM guild_module_settings WHERE guild_id = :gid AND module_key = :mk"),
        {"gid": guild_id, "mk": module_key}
    )
    row = result.fetchone()
    
    if row:
        existing_id, current_version = row[0], row[1] or 1
        new_version = current_version + 1 if publish else current_version
        
        if publish:
            await db.execute(
                text("""UPDATE guild_module_settings 
                        SET enabled = :enabled, config_json = :config, draft_json = NULL, 
                            version = :version, updated_by = :user_id, updated_at = :now
                        WHERE id = :id"""),
                {"enabled": enabled, "config": json.dumps(config), "version": new_version, 
                 "user_id": user_id, "now": now, "id": existing_id}
            )
        else:
            await db.execute(
                text("""UPDATE guild_module_settings 
                        SET draft_json = :draft, updated_by = :user_id, updated_at = :now
                        WHERE id = :id"""),
                {"draft": json.dumps(config), "user_id": user_id, "now": now, "id": existing_id}
            )
        await db.commit()
        return new_version
    else:
        # Insert new
        if publish:
            await db.execute(
                text("""INSERT INTO guild_module_settings (guild_id, module_key, enabled, config_json, version, updated_by, updated_at)
                        VALUES (:gid, :mk, :enabled, :config, 1, :user_id, :now)"""),
                {"gid": guild_id, "mk": module_key, "enabled": enabled, 
                 "config": json.dumps(config), "user_id": user_id, "now": now}
            )
        else:
            await db.execute(
                text("""INSERT INTO guild_module_settings (guild_id, module_key, enabled, draft_json, version, updated_by, updated_at)
                        VALUES (:gid, :mk, :enabled, :draft, 1, :user_id, :now)"""),
                {"gid": guild_id, "mk": module_key, "enabled": enabled,
                 "draft": json.dumps(config), "user_id": user_id, "now": now}
            )
        await db.commit()
        return 1

# ============================================
# Endpoints
# ============================================

@router.get("/modules", response_model=List[ModuleStatus])
async def list_modules(guild_id: str, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """List all available modules with their current status for a guild"""
    modules_list = []
    
    for key, info in MODULES.items():
        config = await get_guild_module_config(db, guild_id, key)
        modules_list.append(ModuleStatus(
            module_key=key,
            display_name=info["display_name"],
            description=info["description"],
            icon=info["icon"],
            category=info["category"],
            enabled=config["enabled"],
            risk_level=info["risk_level"],
            has_draft=config["draft_config"] is not None,
            last_updated=config["updated_at"]
        ))
    
    return modules_list

@router.get("/modules/{module_key}", response_model=ModuleConfig)
async def get_module_config(guild_id: str, module_key: str, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get detailed configuration for a specific module"""
    if module_key not in MODULES:
        raise HTTPException(status_code=404, detail="Module not found")
    
    config = await get_guild_module_config(db, guild_id, module_key)
    
    return ModuleConfig(
        module_key=module_key,
        enabled=config["enabled"],
        config=config["config"],
        last_updated=config["updated_at"] or datetime.utcnow().isoformat(),
        updated_by={"id": config["updated_by"], "username": "User"} if config["updated_by"] else None,
        version=config["version"],
        has_draft=config["draft_config"] is not None,
        draft_config=config["draft_config"]
    )

@router.put("/modules/{module_key}", response_model=ModuleUpdateResponse)
async def update_module_config(
    guild_id: str, 
    module_key: str, 
    body: ModuleUpdateRequest,
    user: User = Depends(get_me), 
    db: AsyncSession = Depends(get_db)
):
    """Update module configuration"""
    if module_key not in MODULES:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Get current config
    current = await get_guild_module_config(db, guild_id, module_key)
    
    # Merge config
    enabled = body.enabled if body.enabled is not None else current["enabled"]
    config = {**current["config"], **(body.config or {})}
    
    # Save
    version = await save_guild_module_config(
        db, guild_id, module_key, enabled, config, 
        user.discord_id, body.publish
    )
    
    # Notify bot if published
    bot_notified = False
    if body.publish:
        bot_notified = await notify_bot(guild_id, module_key, "update")
    
    logger.info(f"Module {module_key} updated for guild {guild_id}", 
                version=version, published=body.publish, user=user.discord_id)
    
    return ModuleUpdateResponse(
        status="success",
        version=version,
        published=body.publish,
        bot_notified=bot_notified
    )

@router.post("/modules/{module_key}/test", response_model=ModuleTestResponse)
async def test_module(
    guild_id: str,
    module_key: str,
    body: ModuleTestRequest,
    user: User = Depends(get_me),
    db: AsyncSession = Depends(get_db)
):
    """Test/simulate module behavior without actually triggering actions"""
    if module_key not in MODULES:
        raise HTTPException(status_code=404, detail="Module not found")
    
    config = await get_guild_module_config(db, guild_id, module_key)
    rules_matched = []
    would_trigger = False
    
    # AutoMod simulation
    if module_key == "automod" and body.content:
        cfg = config["config"]
        
        # Check profanity
        if cfg.get("profanity", {}).get("enabled"):
            bad_words = cfg["profanity"].get("customWords", [])
            for word in bad_words:
                if word.lower() in body.content.lower():
                    rules_matched.append({
                        "rule": "profanity",
                        "reason": f"Yasaklı kelime bulundu: {word}",
                        "action": cfg["profanity"].get("action", "delete")
                    })
                    would_trigger = True
                    break
        
        # Check links
        if cfg.get("links", {}).get("enabled"):
            import re
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, body.content)
            whitelist = cfg["links"].get("whitelist", [])
            for url in urls:
                is_allowed = any(domain in url for domain in whitelist)
                if not is_allowed:
                    rules_matched.append({
                        "rule": "links",
                        "reason": f"İzin verilmeyen link: {url}",
                        "action": cfg["links"].get("action", "delete")
                    })
                    would_trigger = True
                    break
        
        # Check caps
        if cfg.get("caps", {}).get("enabled") and len(body.content) >= cfg["caps"].get("minLength", 10):
            upper_count = sum(1 for c in body.content if c.isupper())
            total_alpha = sum(1 for c in body.content if c.isalpha())
            if total_alpha > 0:
                caps_ratio = (upper_count / total_alpha) * 100
                if caps_ratio >= cfg["caps"].get("threshold", 70):
                    rules_matched.append({
                        "rule": "caps",
                        "reason": f"Aşırı büyük harf: {caps_ratio:.0f}%",
                        "action": cfg["caps"].get("action", "warn")
                    })
                    would_trigger = True
    
    return ModuleTestResponse(
        would_trigger=would_trigger,
        rules_matched=rules_matched,
        preview_response={
            "type": "embed",
            "title": "⚠️ Kural İhlali" if would_trigger else "✅ Uygun",
            "description": rules_matched[0]["reason"] if rules_matched else "Bu mesaj kurallara uygundur."
        } if body.content else None
    )

@router.get("/metrics", response_model=GuildMetrics)
async def get_guild_metrics(guild_id: str, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get guild statistics and metrics"""
    # This would normally query actual data
    # For now, return placeholder data that can be expanded later
    return GuildMetrics(
        members={"total": 0, "online": 0, "new_24h": 0},
        messages={"today": 0, "week": 0},
        moderation={"actions_today": 0, "warnings_active": 0},
        leveling={"active_users": 0, "xp_today": 0}
    )

@router.get("/audit-logs")
async def get_audit_logs(guild_id: str, page: int = 1, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get panel audit logs for the guild"""
    # Would query panel_audit_logs table
    return {"items": [], "total": 0, "page": page, "pages": 1}

@router.get("/bot-events")
async def get_bot_events(guild_id: str, page: int = 1, user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    """Get bot audit events for the guild"""
    # Would query bot_audit_events table
    return {"items": [], "total": 0, "page": page, "pages": 1}
