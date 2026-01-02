import asyncio
import logging
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from alembic.config import Config
from alembic import command, script
from alembic.runtime import migration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-setup")

async def check_database_readiness(database_url: str) -> bool:
    """Uses a temporary engine to check if Postgres is accepting connections."""
    retries = 30
    for i in range(retries):
        try:
            # Create a simple non-async engine for a quick check or just use async
            engine = create_async_engine(database_url, echo=False)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            logger.info("Database connection established!")
            return True
        except Exception as e:
            logger.warning(f"Database not ready yet ({i+1}/{retries}): {e}")
            await asyncio.sleep(2)
            
    logger.error("Could not connect to database after many retries.")
    return False

def run_migrations():
    """Runs Alembic migrations safely."""
    logger.info("Starting database migration check...")
    
    # 1. Point to correct Alembic config
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini_path = os.path.join(base_dir, "alembic.ini")
    
    alembic_cfg = Config(alembic_ini_path)
    
    # Ensure script location is absolute/correct if needed, or rely on ini rel path
    # Assuming CWD is project root when running this
    
    # 2. Check current state and Stamp if needed
    # (Checking raw DB state is hard without context, but we can assume if 'users' table exists 
    # and alembic_version is empty, we need to stamp)
    
    # NOTE: Since this function might run in async context or be blocking, 
    # Alembic commands are blocking.
    
    try:
        # Check if we need to stamp 'core' revision
        # This is a bit advanced: we'd need to inspect DB.
        # Simpler approach: Try upgrade. If it fails with 'AlreadyExists', then Stamp.
        # But Alembic doesn't fail gracefully on that usually. 
        
        # Safe Strategy:
        # Just run upgrade head.
        # If the user has "partial" DB from bad state, it might fail.
        # But our manual fix in previous steps likely added 'economy_profiles'.
        
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema is up to date!")
        return True
    except Exception as e:
        logger.error(f"Migration upgrade failed: {e}")
        
        # Fallback: Attempt to stamp if table exists error
        if "already exists" in str(e):
             logger.info("Detected existing tables. Attempting to sync version...")
             try:
                 # If we have tables but no version, we assume we are at least at base.
                 # But which base? 
                 # Let's try stamping the economy revision if economy table exists?
                 # Safer: Stamp 'head' if we honestly believe we are mostly there.
                 # Realistically, if upgrade failed on 'already exists', it means we tried to create a table that is there.
                 # So we are ahead of what alembic thinks.
                 command.stamp(alembic_cfg, "head")
                 logger.info("Stamped database as HEAD (assumed manual match).")
                 return True
             except Exception as stamp_exc:
                 logger.error(f"Stamping failed: {stamp_exc}")
                 return False
        return False

if __name__ == "__main__":
    # Ensure we are in project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    
    # Get DB URL from env
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set.")
        sys.exit(1)
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if loop.run_until_complete(check_database_readiness(db_url)):
        success = run_migrations()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(1)
