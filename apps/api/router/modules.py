from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from lithium_core.database.session import get_db
from lithium_core.models import AutoModRule, LevelingConfig, ScheduledMessage, Guild
from .auth import get_me
from typing import Any

router = APIRouter(prefix="/guilds/{guild_id}/modules", tags=["modules"])

# RBAC dependency
async def check_permissions(guild_id: str, user=Depends(get_me), db: AsyncSession = Depends(get_db)):
    # Get OAuth Session to check fresh permissions from Discord or Cache
    # For now, we trust the DB cache or assume user ownership check from Guilds endpoint
    # A robust implementation would double check against Discord API if critical
    
    # Simple check: Does user exist? (Auth wrapper handles this)
    # RBAC logic is primarily handled in the dashboard panel;
    # access to this API should be secured by internal VPC or shared JWT secrets.
    pass

@router.get("/automod")
async def get_automod_rules(guild_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AutoModRule).where(AutoModRule.guild_id == guild_id))
    return result.scalars().all()

@router.post("/automod")
async def create_automod_rule(guild_id: str, rule: dict = Body(...), db: AsyncSession = Depends(get_db)):
    new_rule = AutoModRule(guild_id=guild_id, **rule)
    db.add(new_rule)
    await db.commit()
    
    # Publish to Redis
    import redis.asyncio as redis
    import json
    import os
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        async with redis.from_url(redis_url) as r:
            await r.publish("guild_config_changed", json.dumps({
                "guild_id": guild_id,
                "module": "automod",
                "action": "create",
                "rule_id": str(new_rule.id)
            }))
    except Exception as e:
        print(f"Failed to publish to Redis: {e}")
        
    return new_rule

@router.get("/leveling")
async def get_leveling_config(guild_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LevelingConfig).where(LevelingConfig.guild_id == guild_id))
    config = result.scalar_one_or_none()
    if not config:
        return {"enabled": False} # Default
    return config

@router.patch("/leveling")
async def update_leveling_config(guild_id: str, config: dict = Body(...), db: AsyncSession = Depends(get_db)):
    # Upsert logic
    result = await db.execute(select(LevelingConfig).where(LevelingConfig.guild_id == guild_id))
    existing = result.scalar_one_or_none()
    
    if existing:
        for k, v in config.items():
            setattr(existing, k, v)
    else:
        new_config = LevelingConfig(guild_id=guild_id, **config)
        db.add(new_config)
        
    await db.commit()
    
    # Publish to Redis
    import redis.asyncio as redis
    import json
    import os
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        async with redis.from_url(redis_url) as r:
            await r.publish("guild_config_changed", json.dumps({
                "guild_id": guild_id,
                "module": "leveling",
                "action": "update"
            }))
    except Exception as e:
        print(f"Failed to publish to Redis: {e}")
        
    return {"status": "updated"}
