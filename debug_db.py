import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import logging

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set!")
        return
        
    print(f"Connecting to DB...") 
    try:
        engine = create_async_engine(url)
        
        async with engine.connect() as conn:
            print("\n--- CONNECTION SUCCESSFUL ---\n")
            
            # List tables
            result = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"))
            tables = result.fetchall()
            
            print(f"Found {len(tables)} tables:")
            for t in tables:
                print(f" - {t[0]}")
                
            print("\n---------------------------\n")
            
            # Check Alembic Version
            try:
                v = await conn.execute(text("SELECT * FROM alembic_version"))
                version = v.scalar_one_or_none()
                print(f"Current Migration Version: {version}")
            except Exception as e:
                print("Could not read alembic_version (table might be missing)")
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
