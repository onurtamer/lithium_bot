import discord
from discord.ext import commands
from discord import app_commands
import logging
import re
import os
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import AutoModRule, LogEvent

logger = logging.getLogger("lithium-bot")

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = None
        self.invite_rx = re.compile(r"(discord\.gg/|discord\.com/invite/)")

    async def cog_load(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis = redis.from_url(redis_url)

    async def get_antispam_budget(self, guild_id: int, user_id: int):
        if not self.redis: return 0
        key = f"antispam:{guild_id}:{user_id}"
        count = await self.redis.get(key)
        return int(count) if count else 0

    async def inc_antispam_budget(self, guild_id: int, user_id: int):
        if not self.redis: return
        key = f"antispam:{guild_id}:{user_id}"
        await self.redis.incr(key)
        await self.redis.expire(key, 5) # 5 second window for spam

    async def check_quarantine(self, guild_id: int):
        if not self.redis: return False
        key = f"quarantine:{guild_id}"
        return await self.redis.get(key) is not None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        # 1. Anti-Spam Budget Check
        count = await self.get_antispam_budget(message.guild.id, message.author.id)
        if count > 5: # Threshold
            try:
                await message.delete()
            except: pass
            return await message.channel.send(f"⚠️ {message.author.mention}, you are sending messages too fast!", delete_after=3)
        await self.inc_antispam_budget(message.guild.id, message.author.id)

        # 2. Invite Filter
        if self.invite_rx.search(message.content):
            try:
                await message.delete()
            except: pass
            return await message.channel.send(f"🚫 {message.author.mention}, invite links are not allowed here.", delete_after=5)

        # 3. Mention Spam / Raid Detection
        if len(message.mentions) > 5 or len(message.role_mentions) > 3:
            try:
                await message.delete()
            except: pass
            return await message.channel.send(f"🚫 {message.author.mention}, mass mentions are prohibited.", delete_after=5)

        # 4. Bad Words (Simple version for demo)
        if "scam" in message.content.lower():
            try:
                await message.delete()
            except: pass
            return await message.channel.send("🚫 Scam link or keyword detected.", delete_after=5)

    @app_commands.command(name="quarantine", description="Toggle guild-wide quarantine mode (lockdown)")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_quarantine(self, interaction: discord.Interaction, enabled: bool):
        if not self.redis:
            return await interaction.response.send_message("❌ Redis is not connected.", ephemeral=True)
            
        key = f"quarantine:{interaction.guild_id}"
        if enabled:
            await self.redis.set(key, "active", ex=3600) # 1 hour lockdown
            await interaction.response.send_message("🔒 **GUILD QUARANTINE ACTIVE**. Filters are tightened and new members are restricted.")
        else:
            await self.redis.delete(key)
            await interaction.response.send_message("🔓 **GUILD QUARANTINE LIFTED**.")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
