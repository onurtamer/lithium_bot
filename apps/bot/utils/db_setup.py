import asyncio
import logging
import os
import sys
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from lithium_core.models import Base  # Import consolidated models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-setup")

async def sync_schema(engine):
    """
    Synchronizes the database schema with the SQLAlchemy models.
    1. Creates missing tables (safe, built-in).
    2. Adds missing columns to existing tables (custom logic).
    Values data safety over strict migration history.
    """
    async with engine.begin() as conn:
        # 1. Create Missing Tables
        logger.info("1. Checking for missing tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 2. Check for Missing Columns (Schema Drift)
        logger.info("2. Checking for missing columns (Schema Drift)...")
        await conn.run_sync(_sync_columns)
        
    logger.info("✅ Database schema synchronized successfully.")

def _sync_columns(conn):
    """
    Inspects DB and adds missing columns safely.
    Run this synchronously inside run_sync.
    """
    inspector = inspect(conn)
    
    for table_name, model_table in Base.metadata.tables.items():
        # Skip if table doesn't exist (create_all should have handled it, but safety first)
        if not inspector.has_table(table_name):
            continue
            
        # Get existing columns in DB
        db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        
        # Check model columns
        for column in model_table.columns:
            if column.name not in db_columns:
                logger.warning(f"Feature update detected: Adding missing column '{column.name}' to table '{table_name}'")
                
                # Construct ALTER TABLE statement
                # We need the SQL type compilation
                col_type = column.type.compile(conn.dialect)
                
                # Check for nullable/defaults to ensure valid SQL
                nullable = "NULL" if column.nullable else "NOT NULL"
                default = ""
                if column.server_default:
                    # This is tricky as server_default can be an object. 
                    # For simplicity in this auto-healer, we adding columns as NULLable first usually 
                    # or strictly if we can render the default.
                    # To avoid complex SQL errors on existing data, we default to adding as NULL
                    # unless it's critical. 
                    pass

                # Safer approach for addition: Add as NULL first (unless default provided)
                # If the user has data, adding NOT NULL without default fails.
                
                try:
                    # Simple ADD COLUMN. 
                    # NOTE: This does not handle complex constraints (FK per column) perfectly in raw SQL, 
                    # but good enough for primitives.
                    stmt = f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {col_type}'
                    conn.execute(text(stmt))
                    logger.info(f" -> Added column {column.name}")
                except Exception as e:
                    logger.error(f"Failed to auto-add column {column.name} to {table_name}: {e}")

async def run_migrations_async():
    """
    Main entry point called by bot setup_hook.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL missing.")
        return

    # Ensure async driver for SQLAlchemy AsyncEngine
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    try:
        engine = create_async_engine(db_url, echo=False)
        await sync_schema(engine)
        await engine.dispose()
    except Exception as e:
        logger.error(f"Critical DB Sync Error: {e}")
        # We re-raise so the bot knows DB is broken, but logging it is helpful.
        raise e

if __name__ == "__main__":
    # Standalone test
    asyncio.run(run_migrations_async())
