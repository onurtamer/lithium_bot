import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import (
    Reminder, StickyMessage, AFKState, AutoResponder, 
    VoiceConfig, StarboardConfig, Guild
)

logger = logging.getLogger("lithium-bot")

class AdvancedUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = None

    async def cog_load(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis = redis.from_url(redis_url)

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.id == str(message.guild.id))
            guild_config = (await db.execute(stmt)).scalar_one_or_none()
            if not guild_config:
                return

            # 1. AFK Logic
            if guild_config.afk_enabled:
                stmt = select(AFKState).where(AFKState.user_id == str(message.author.id), AFKState.guild_id == str(message.guild.id))
                afk = (await db.execute(stmt)).scalar_one_or_none()
                if afk:
                    await db.delete(afk)
                    await db.commit()
                    await message.channel.send(f"👋 Welcome back {message.author.mention}, I removed your AFK status.", delete_after=5)

                if message.mentions:
                    for user in message.mentions:
                        stmt = select(AFKState).where(AFKState.user_id == str(user.id), AFKState.guild_id == str(message.guild.id))
                        afk = (await db.execute(stmt)).scalar_one_or_none()
                        if afk:
                            await message.channel.send(f"💤 {user.name} is AFK: {afk.message or 'No reason provided'}", delete_after=10)

            # 2. Auto Responder
            if guild_config.auto_responder_enabled:
                stmt = select(AutoResponder).where(AutoResponder.guild_id == str(message.guild.id))
                responders = (await db.execute(stmt)).scalars().all()
                for ar in responders:
                    if ar.trigger.lower() in message.content.lower():
                        key = f"ar_cooldown:{message.guild.id}:{ar.id}"
                        if not await self.redis.get(key):
                            await message.channel.send(ar.response)
                            await self.redis.set(key, "1", ex=ar.cooldown)
                            break

            # 3. Sticky Message Handler
            if guild_config.sticky_messages_enabled:
                stmt = select(StickyMessage).where(StickyMessage.channel_id == str(message.channel.id))
                sticky = (await db.execute(stmt)).scalar_one_or_none()
                if sticky:
                    if sticky.last_message_id:
                        try:
                            old_msg = await message.channel.fetch_message(int(sticky.last_message_id))
                            await old_msg.delete()
                        except: pass
                    
                    new_msg = await message.channel.send(f"📌 **Sticky Message**\n{sticky.content}")
                    sticky.last_message_id = str(new_msg.id)
                    await db.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return

        async with AsyncSessionLocal() as db:
            guild_stmt = select(Guild).where(Guild.id == str(payload.guild_id))
            guild_config = (await db.execute(guild_stmt)).scalar_one_or_none()
            if not guild_config or not guild_config.starboard_enabled:
                return

            stmt = select(StarboardConfig).where(StarboardConfig.guild_id == str(payload.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            if not config:
                return

            channel = self.bot.get_channel(payload.channel_id)
            if not channel: return
            message = await channel.fetch_message(payload.message_id)
            
            star_reaction = discord.utils.get(message.reactions, emoji="⭐")
            if star_reaction and star_reaction.count >= config.threshold:
                # Move to starboard channel
                starboard_channel = self.bot.get_channel(int(config.channel_id))
                if not starboard_channel: return

                # Prevent double posting
                key = f"starboard_posted:{message.id}"
                if await self.redis.get(key):
                    return

                embed = discord.Embed(description=message.content, color=discord.Color.gold())
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                embed.add_field(name="Source", value=f"[Jump to Message]({message.jump_url})")
                
                # Check for attachments
                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)
                
                await starboard_channel.send(embed=embed)
                await self.redis.set(key, "1", ex=60*60*24*7) # Cache for 1 week

    @app_commands.command(name="afk", description="Set your AFK status")
    async def afk(self, interaction: discord.Interaction, message: str = "AFK"):
        async with AsyncSessionLocal() as db:
            afk = AFKState(
                user_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id),
                message=message
            )
            db.add(afk)
            await db.commit()
        await interaction.response.send_message(f"💤 You are now AFK: {message}", ephemeral=True)

    # --- REMINDERS ---
    @app_commands.command(name="remind", description="Set a reminder")
    async def remind(self, interaction: discord.Interaction, time: str, content: str):
        # Very simple parser: "10m", "1h", etc.
        amount = int(time[:-1])
        unit = time[-1].lower()
        delta = timedelta(minutes=amount) if unit == 'm' else timedelta(hours=amount) if unit == 'h' else timedelta(days=amount)
        
        remind_at = datetime.utcnow() + delta
        
        async with AsyncSessionLocal() as db:
            reminder = Reminder(
                user_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id),
                channel_id=str(interaction.channel_id),
                content=content,
                remind_at=remind_at
            )
            db.add(reminder)
            await db.commit()
            
        await interaction.response.send_message(f"⏰ Okay, I will remind you about '{content}' in {time}.", ephemeral=True)

    # --- STICKY MESSAGES ---
    @app_commands.command(name="sticky", description="Set a sticky message for this channel")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def sticky(self, interaction: discord.Interaction, content: str):
        async with AsyncSessionLocal() as db:
            stmt = select(StickyMessage).where(StickyMessage.channel_id == str(interaction.channel_id))
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                existing.content = content
            else:
                sticky = StickyMessage(
                    guild_id=str(interaction.guild_id),
                    channel_id=str(interaction.channel_id),
                    content=content
                )
                db.add(sticky)
            await db.commit()
        await interaction.response.send_message(f"📌 Sticky message set for this channel.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message_sticky_handler(self, message: discord.Message):
        # Already handled in on_message above
        pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel:
            async with AsyncSessionLocal() as db:
                stmt = select(VoiceConfig).where(VoiceConfig.guild_id == str(member.guild.id))
                config = (await db.execute(stmt)).scalar_one_or_none()
                if config and str(after.channel.id) == config.category_id: # Usually use a specific channel ID
                    # Create new channel
                    category = after.channel.category
                    name = config.channel_name_tpl.format(user=member.name)
                    new_channel = await member.guild.create_voice_channel(name, category=category)
                    await member.move_to(new_channel)
                    
                    # Track in Redis to delete later
                    key = f"temp_vc:{new_channel.id}"
                    await self.redis.set(key, "1")

        if before.channel:
            key = f"temp_vc:{before.channel.id}"
            if await self.redis.get(key):
                if len(before.channel.members) == 0:
                    await before.channel.delete()
                    await self.redis.delete(key)

async def setup(bot):
    await bot.add_cog(AdvancedUtils(bot))
