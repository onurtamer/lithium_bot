import discord
from discord.ext import commands
import logging
from sqlalchemy import select
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import Guild, WelcomeConfig, EmbedConfig

logger = logging.getLogger("lithium-bot")

class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.discord_id == str(member.guild.id))
            guild_config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not guild_config or not guild_config.welcome_enabled:
                return

            stmt = select(WelcomeConfig).where(WelcomeConfig.guild_id == str(member.guild.id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            if not config or not config.channel_id:
                return

            channel = member.guild.get_channel(int(config.channel_id))
            if not channel:
                return

            # Auto Role
            if config.auto_role_id:
                role = member.guild.get_role(int(config.auto_role_id))
                if role:
                    try: await member.add_roles(role)
                    except: pass

            welcome_text = config.welcome_message.format(user=member.mention, server=member.guild.name)
            
            if config.use_embed:
                embed = discord.Embed(
                    description=welcome_text,
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)
            else:
                await channel.send(welcome_text)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
