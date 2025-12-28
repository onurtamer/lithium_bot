import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.guild import Guild, ModerationConfig, WelcomeConfig

async def seed():
    async with AsyncSessionLocal() as db:
        # Check if demo guild exists
        # This is just a placeholder seed
        print("Seeding database...")
        # await db.execute(...)
        await db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
