import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.leveling import UserLevel as LevelingState, LevelingConfig, LevelReward
from lithium_core.models.core import Guild
from sqlalchemy import select
from typing import Optional
import time
import math

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def get_xp_for_level(self, level: int):
        return 5 * (level ** 2) + (50 * level) + 100

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.discord_id == str(message.guild.id))
            guild_config = (await db.execute(stmt)).scalar_one_or_none()
            if not guild_config or not guild_config.leveling_enabled:
                return
            
        now = time.time()
        user_key = f"{message.guild.id}-{message.author.id}"
        
        if user_key in self.cooldowns and now - self.cooldowns[user_key] < 60:
            return
            
        self.cooldowns[user_key] = now
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(LevelingState).where(LevelingState.guild_id == str(message.guild.id), LevelingState.user_id == str(message.author.id)))
            state = result.scalar_one_or_none()
            
            if not state:
                state = LevelingState(guild_id=str(message.guild.id), user_id=str(message.author.id), xp=0, level=0)
                db.add(state)
            
            state.xp += 15 # default xp
            
            xp_needed = self.get_xp_for_level(state.level)
            if state.xp >= xp_needed:
                state.level += 1
                state.xp = 0 # reset or keep remainder? usually reset or subtract.
                await message.channel.send(f"GG {message.author.mention}, you leveled up to **Level {state.level}**!")
                
                # Role Rewards Check
                rewards_res = await db.execute(select(LevelReward).where(LevelReward.guild_id == str(message.guild.id), LevelReward.level <= state.level))
                for reward in rewards_res.scalars().all():
                    role = message.guild.get_role(int(reward.role_id))
                    if role and role not in message.author.roles:
                        await message.author.add_roles(role)
            
            await db.commit()

    @app_commands.command(name="rank", description="Check your or someone's rank")
    async def rank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        member = member or interaction.user
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(LevelingState).where(LevelingState.guild_id == str(interaction.guild_id), LevelingState.user_id == str(member.id)))
            state = result.scalar_one_or_none()
            
            if not state:
                return await interaction.response.send_message("No rank data found for this user.")
                
            xp_needed = self.get_xp_for_level(state.level)
            await interaction.response.send_message(f"**{member.name}'s Rank**\nLevel: {state.level}\nXP: {state.xp}/{xp_needed}")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
