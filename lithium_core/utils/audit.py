from sqlalchemy import insert
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import AuditLog
import logging

logger = logging.getLogger("lithium-core")

async def log_audit(guild_id: str, user_id: str, action: str, target: str, changes: dict = None):
    """
    Logs an action to the audit_logs table for traceability.
    """
    try:
        async with AsyncSessionLocal() as db:
            audit = AuditLog(
                guild_id=guild_id,
                user_id=user_id,
                action=action,
                target=target,
                changes=changes
            )
            db.add(audit)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")

def log_audit_sync(guild_id: str, user_id: str, action: str, target: str, changes: dict = None):
    """
    Sync version of log_audit for Django/Sync contexts.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    import os
    
    # Simple sync engine for utility
    engine = create_engine(os.getenv("DATABASE_URL").replace("+asyncpg", ""))
    try:
        with Session(engine) as session:
            audit = AuditLog(
                guild_id=guild_id,
                user_id=user_id,
                action=action,
                target=target,
                changes=changes
            )
            session.add(audit)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to log audit event (sync): {e}")
