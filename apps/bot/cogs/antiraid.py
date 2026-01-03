import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import Guild, QuarantineConfig, QuarantineLog

logger = logging.getLogger("lithium-bot")

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.joins = {} # Cache joins: {guild_id: [datetime, ...]}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.discord_id == str(member.guild.id))
            guild = (await db.execute(stmt)).scalar_one_or_none()
            
            if not guild or not guild.quarantine_enabled:
                return

            stmt = select(QuarantineConfig).where(QuarantineConfig.guild_id == str(member.guild.id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            if not config:
                return

            # 1. Join Rate Check
            now = datetime.utcnow()
            guild_id = str(member.guild.id)
            if guild_id not in self.joins:
                self.joins[guild_id] = []
            
            # Clean old joins
            self.joins[guild_id] = [j for j in self.joins[guild_id] if j > now - timedelta(minutes=1)]
            self.joins[guild_id].append(now)

            triggered = False
            reason = ""

            if len(self.joins[guild_id]) > config.max_joins_per_minute:
                triggered = True
                reason = "Join rate exceeded"

            # 2. Account Age Check
            if not triggered and config.min_account_age_days > 0:
                age = (now - member.created_at.replace(tzinfo=None)).days
                if age < config.min_account_age_days:
                    triggered = True
                    reason = f"Account too young ({age} days)"

            # 3. Avatar Check
            if not triggered and config.require_avatar and not member.avatar:
                triggered = True
                reason = "No avatar"

            if triggered:
                await self.take_action(member, config, reason)

    async def take_action(self, member: discord.Member, config: QuarantineConfig, reason: str):
        action = config.action
        try:
            if action == "KICK":
                await member.kick(reason=f"[Anti-Raid] {reason}")
            elif action == "BAN":
                await member.ban(reason=f"[Anti-Raid] {reason}")
            elif action == "QUARANTINE_ROLE" and config.quarantine_role_id:
                role = member.guild.get_role(int(config.quarantine_role_id))
                if role:
                    await member.add_roles(role, reason=f"[Anti-Raid] {reason}")

            # Log to DB
            async with AsyncSessionLocal() as db:
                log = QuarantineLog(
                    guild_id=str(member.guild.id),
                    user_id=str(member.id),
                    reason=reason,
                    action_taken=action
                )
                db.add(log)
                await db.commit()
                
            logger.info(f"Anti-Raid action {action} on {member} in {member.guild.name} for {reason}")
        except Exception as e:
            logger.error(f"Failed to take Anti-Raid action on {member}: {e}")

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
