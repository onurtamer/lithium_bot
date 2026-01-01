import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from sqlalchemy import Column, Integer, String, Text, Boolean, select
from lithium_core.models.base import Base, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import logging

logger = logging.getLogger("lithium-bot")

# Model for Welcome Config
class WelcomeConfig(Base, TimestampMixin):
    __tablename__ = "welcome_configs"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    welcome_channel_id: Mapped[str] = mapped_column(String, nullable=True)
    goodbye_channel_id: Mapped[str] = mapped_column(String, nullable=True)
    welcome_message: Mapped[str] = mapped_column(Text, nullable=True)
    goodbye_message: Mapped[str] = mapped_column(Text, nullable=True)
    embed_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_message(self, message: str, member: discord.Member) -> str:
        """Replace placeholders with actual values"""
        if not message:
            return None
        return message.replace(
            "{user}", member.mention
        ).replace(
            "{username}", member.name
        ).replace(
            "{server}", member.guild.name
        ).replace(
            "{count}", str(member.guild.member_count)
        )

    async def get_config(self, guild_id: int) -> WelcomeConfig:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == str(guild_id)))
            return result.scalar_one_or_none()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = await self.get_config(member.guild.id)
        if not config or not config.welcome_channel_id:
            return

        channel = self.bot.get_channel(int(config.welcome_channel_id))
        if not channel:
            return

        message = self.format_message(
            config.welcome_message or "Hoş geldin {user}! Sunucumuza katıldığın için teşekkürler. Sen {count}. üyemizsin! 🎉",
            member
        )

        if config.embed_enabled:
            embed = discord.Embed(
                title="👋 Hoş Geldin!",
                description=message,
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"{member.guild.name} • Üye #{member.guild.member_count}")
            await channel.send(embed=embed)
        else:
            await channel.send(message)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = await self.get_config(member.guild.id)
        if not config or not config.goodbye_channel_id:
            return

        channel = self.bot.get_channel(int(config.goodbye_channel_id))
        if not channel:
            return

        message = self.format_message(
            config.goodbye_message or "Güle güle {username}! Umarız tekrar görüşürüz. 👋",
            member
        )

        if config.embed_enabled:
            embed = discord.Embed(
                title="👋 Güle Güle!",
                description=message,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        else:
            await channel.send(message)

    @app_commands.command(name="welcome_channel", description="Hoş geldin kanalını ayarla")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == str(interaction.guild_id)))
            config = result.scalar_one_or_none()
            
            if not config:
                config = WelcomeConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.welcome_channel_id = str(channel.id)
            await db.commit()

        await interaction.response.send_message(f"✅ Hoş geldin kanalı {channel.mention} olarak ayarlandı.", ephemeral=True)

    @app_commands.command(name="goodbye_channel", description="Güle güle kanalını ayarla")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == str(interaction.guild_id)))
            config = result.scalar_one_or_none()
            
            if not config:
                config = WelcomeConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.goodbye_channel_id = str(channel.id)
            await db.commit()

        await interaction.response.send_message(f"✅ Güle güle kanalı {channel.mention} olarak ayarlandı.", ephemeral=True)

    @app_commands.command(name="welcome_message", description="Hoş geldin mesajını ayarla")
    @app_commands.describe(message="Mesaj ({user}, {username}, {server}, {count} kullanılabilir)")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_message(self, interaction: discord.Interaction, message: str):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == str(interaction.guild_id)))
            config = result.scalar_one_or_none()
            
            if not config:
                config = WelcomeConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.welcome_message = message
            await db.commit()

        await interaction.response.send_message(f"✅ Hoş geldin mesajı güncellendi:\n```{message}```", ephemeral=True)

    @app_commands.command(name="goodbye_message", description="Güle güle mesajını ayarla")
    @app_commands.describe(message="Mesaj ({user}, {username}, {server}, {count} kullanılabilir)")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_message(self, interaction: discord.Interaction, message: str):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == str(interaction.guild_id)))
            config = result.scalar_one_or_none()
            
            if not config:
                config = WelcomeConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.goodbye_message = message
            await db.commit()

        await interaction.response.send_message(f"✅ Güle güle mesajı güncellendi:\n```{message}```", ephemeral=True)

    @app_commands.command(name="welcome_embed", description="Embed kullanımını aç/kapat")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_embed(self, interaction: discord.Interaction, enabled: bool):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == str(interaction.guild_id)))
            config = result.scalar_one_or_none()
            
            if not config:
                config = WelcomeConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.embed_enabled = enabled
            await db.commit()

        status = "açık" if enabled else "kapalı"
        await interaction.response.send_message(f"✅ Embed kullanımı {status}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
