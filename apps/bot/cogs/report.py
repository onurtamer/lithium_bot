import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from sqlalchemy import Column, Integer, String, Text, DateTime, select
from lithium_core.models.base import Base, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import logging

logger = logging.getLogger("lithium-bot")

# Model for Reports
class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    reporter_id: Mapped[str] = mapped_column(String, index=True)
    reported_id: Mapped[str] = mapped_column(String, index=True)
    reason: Mapped[str] = mapped_column(Text)
    evidence_url: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="OPEN")  # OPEN, RESOLVED, DISMISSED

# Model for Report Channel Config
class ReportConfig(Base, TimestampMixin):
    __tablename__ = "report_configs"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    channel_id: Mapped[str] = mapped_column(String, nullable=True)


class ReportView(discord.ui.View):
    def __init__(self, report_id: int):
        super().__init__(timeout=None)
        self.report_id = report_id

    @discord.ui.button(label="✅ Çözüldü", style=discord.ButtonStyle.success, custom_id="report_resolve")
    async def resolve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Report).where(Report.id == self.report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = "RESOLVED"
                await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=f"✅ Çözüldü - {interaction.user.name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Rapor çözüldü olarak işaretlendi.", ephemeral=True)

    @discord.ui.button(label="❌ Reddet", style=discord.ButtonStyle.danger, custom_id="report_dismiss")
    async def dismiss(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Report).where(Report.id == self.report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = "DISMISSED"
                await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.light_grey()
        embed.set_footer(text=f"❌ Reddedildi - {interaction.user.name}")
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Rapor reddedildi.", ephemeral=True)


class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_report_channel(self, guild_id: int) -> discord.TextChannel:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ReportConfig).where(ReportConfig.guild_id == str(guild_id)))
            config = result.scalar_one_or_none()
            if config and config.channel_id:
                return self.bot.get_channel(int(config.channel_id))
        return None

    @app_commands.command(name="report", description="Bir kullanıcıyı kural ihlali için raporla")
    @app_commands.describe(
        user="Raporlanacak kullanıcı",
        reason="İhlal sebebi",
        evidence="Kanıt linki (opsiyonel)"
    )
    async def report(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: str = None):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendinizi raporlayamazsınız.", ephemeral=True)
        if user.bot:
            return await interaction.response.send_message("❌ Botları raporlayamazsınız.", ephemeral=True)

        report_channel = await self.get_report_channel(interaction.guild_id)
        if not report_channel:
            return await interaction.response.send_message("❌ Rapor kanalı ayarlanmamış! Admin `/report_setup` kullanmalı.", ephemeral=True)

        async with AsyncSessionLocal() as db:
            report = Report(
                guild_id=str(interaction.guild_id),
                reporter_id=str(interaction.user.id),
                reported_id=str(user.id),
                reason=reason,
                evidence_url=evidence,
                status="OPEN"
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            report_id = report.id

        embed = discord.Embed(
            title="🚨 Yeni Rapor",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Raporlayan", value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
        embed.add_field(name="Raporlanan", value=f"{user.mention} ({user.id})", inline=True)
        embed.add_field(name="Sebep", value=reason, inline=False)
        if evidence:
            embed.add_field(name="Kanıt", value=evidence, inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Rapor ID: #{report_id}")

        view = ReportView(report_id)
        await report_channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Raporunuz iletildi. Teşekkür ederiz!", ephemeral=True)

    @app_commands.command(name="report_setup", description="Rapor kanalını ayarla")
    @app_commands.checks.has_permissions(administrator=True)
    async def report_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ReportConfig).where(ReportConfig.guild_id == str(interaction.guild_id)))
            config = result.scalar_one_or_none()
            
            if not config:
                config = ReportConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.channel_id = str(channel.id)
            await db.commit()

        await interaction.response.send_message(f"✅ Rapor kanalı {channel.mention} olarak ayarlandı.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReportSystem(bot))
