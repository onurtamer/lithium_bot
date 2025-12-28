import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
from datetime import datetime
from sqlalchemy import select, delete, update
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import Guild, ReactionRoleMenu, ScheduledMessage, CustomCommand

logger = logging.getLogger("lithium-bot")

class SocialFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler.start()

    def cog_unload(self):
        self.scheduler.cancel()

    @tasks.loop(minutes=1)
    async def scheduler(self):
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            stmt = select(ScheduledMessage).where(
                ScheduledMessage.enabled == True,
                ScheduledMessage.run_at <= now
            )
            messages = (await db.execute(stmt)).scalars().all()
            for msg in messages:
                channel = self.bot.get_channel(int(msg.channel_id))
                if channel:
                    await channel.send(msg.content)
                
                # Update last_run or delete
                msg.last_run_at = now
                if not msg.cron: # One-off
                    msg.enabled = False
            
            await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Custom Commands
        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.id == str(message.guild.id))
            guild = (await db.execute(stmt)).scalar_one_or_none()
            if not guild or not guild.custom_commands_enabled:
                return

            if message.content.startswith("!"): # Prefix could be dynamic
                cmd_name = message.content[1:].split()[0].lower()
                stmt = select(CustomCommand).where(CustomCommand.guild_id == str(message.guild.id), CustomCommand.name == cmd_name)
                cmd = (await db.execute(stmt)).scalar_one_or_none()
                if cmd:
                    await message.channel.send(cmd.response)

    @app_commands.command(name="cc-add", description="Add a custom command")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def cc_add(self, interaction: discord.Interaction, name: str, response: str):
        async with AsyncSessionLocal() as db:
            cmd = CustomCommand(guild_id=str(interaction.guild_id), name=name.lower(), response=response)
            db.add(cmd)
            await db.commit()
        await interaction.response.send_message(f"✅ Custom command `!{name}` added.", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionAddEvent):
        if payload.member.bot: return
        
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(ReactionRoleMenu.message_id == str(payload.message_id))
            menu = (await db.execute(stmt)).scalar_one_or_none()
            if not menu: return
            
            emoji_str = str(payload.emoji)
            if emoji_str in menu.options:
                role_id = int(menu.options[emoji_str])
                role = payload.member.guild.get_role(role_id)
                if role:
                    await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionRemoveEvent):
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(ReactionRoleMenu.message_id == str(payload.message_id))
            menu = (await db.execute(stmt)).scalar_one_or_none()
            if not menu: return
            
            guild = self.bot.get_guild(payload.guild_id)
            if not guild: return
            member = guild.get_member(payload.user_id)
            if not member or member.bot: return

            emoji_str = str(payload.emoji)
            if emoji_str in menu.options:
                role_id = int(menu.options[emoji_str])
                role = guild.get_role(role_id)
                if role:
                    await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(SocialFeatures(bot))
