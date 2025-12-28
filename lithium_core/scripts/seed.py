import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import User, Guild, AutoModRule, ScheduledMessage, UserLevel
from sqlalchemy import select

async def seed_data():
    async with AsyncSessionLocal() as db:
        print("Seeding data...")
        
        # 1. Admin User
        admin_id = "ADMIN_DISCORD_ID_PLACEHOLDER" # Replace or load from env
        result = await db.execute(select(User).where(User.discord_id == admin_id))
        if not result.scalar_one_or_none():
            admin = User(discord_id=admin_id, username="AdminUser", avatar_url="")
            db.add(admin)
            print("Created Admin User")

        # 2. Demo Guild
        guild_id = "DEMO_GUILD_ID"
        result = await db.execute(select(Guild).where(Guild.discord_id == guild_id))
        if not result.scalar_one_or_none():
            guild = Guild(discord_id=guild_id, name="Lithium Demo Server", owner_id=admin_id)
            db.add(guild)
            print("Created Demo Guild")
            
        # 3. AutoMod Rule
        result = await db.execute(select(AutoModRule).where(AutoModRule.guild_id == guild_id))
        if not result.scalars().first():
            rule = AutoModRule(
                guild_id=guild_id,
                rule_type="BAD_WORDS",
                config={"words": ["bad", "evil"], "regex": []},
                actions={"type": "DELETE"},
                enabled=True
            )
            db.add(rule)
            print("Created AutoMod Rule")
            
        await db.commit()
        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
