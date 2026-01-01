"""
Safe Mode Handler - Break-glass and safe mode commands
"""
import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.services.governance_service import GovernanceService
from lithium_core.services.case_service import CaseService
from datetime import datetime
import logging

logger = logging.getLogger("lithium-bot")


class SafeModeHandler(commands.Cog):
    """
    Safe Mode ve Break-Glass komutları
    - Owner only
    - Tüm enforcement'ı durdurur
    - Sadece log tutar
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_owner(self, interaction: discord.Interaction) -> bool:
        """Check if user is server owner"""
        return interaction.user.id == interaction.guild.owner_id
    
    # ==================== SAFE MODE ====================
    
    safemode = app_commands.Group(name="safe-mode", description="Safe mode komutları (Owner only)")
    
    @safemode.command(name="enable", description="Safe mode'u aktive et - tüm enforcement durur")
    @app_commands.describe(reason="Safe mode sebebi")
    async def safemode_enable(self, interaction: discord.Interaction, reason: str):
        if not self.is_owner(interaction):
            return await interaction.response.send_message(
                "❌ Bu komut sadece sunucu sahibi tarafından kullanılabilir!",
                ephemeral=True
            )
        
        await interaction.response.defer(ephemeral=True)
        
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            case_svc = CaseService(db)
            
            config = await governance_svc.enable_safe_mode(
                str(interaction.guild_id),
                str(interaction.user.id),
                reason
            )
            
            # Audit log
            await case_svc.log_audit_event(
                guild_id=str(interaction.guild_id),
                event_type="safe_mode",
                actor_id=str(interaction.user.id),
                actor_type="owner",
                action="enable",
                details={"reason": reason}
            )
            
            # Alert channel
            if config.alerts_channel_id:
                alert_channel = self.bot.get_channel(int(config.alerts_channel_id))
                if alert_channel:
                    embed = discord.Embed(
                        title="🛑 SAFE MODE AKTİF",
                        description=f"**Sebep:** {reason}\n\nTüm otomatik enforcement durduruldu.\nBot sadece log tutmaya devam edecek.",
                        color=discord.Color.dark_red(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Aktive Eden", value=interaction.user.mention, inline=True)
                    embed.set_footer(text="Safe mode'u kapatmak için /safe-mode disable kullanın")
                    
                    await alert_channel.send(embed=embed)
        
        await interaction.followup.send(
            f"✅ Safe mode aktive edildi.\n"
            f"**Sebep:** {reason}\n\n"
            f"⚠️ Tüm otomatik enforcement durduruldu. Bot sadece log tutuyor.",
            ephemeral=True
        )
    
    @safemode.command(name="disable", description="Safe mode'u deaktive et - normal operasyona dön")
    async def safemode_disable(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await interaction.response.send_message(
                "❌ Bu komut sadece sunucu sahibi tarafından kullanılabilir!",
                ephemeral=True
            )
        
        await interaction.response.defer(ephemeral=True)
        
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            case_svc = CaseService(db)
            
            config = await governance_svc.disable_safe_mode(str(interaction.guild_id))
            
            # Audit log
            await case_svc.log_audit_event(
                guild_id=str(interaction.guild_id),
                event_type="safe_mode",
                actor_id=str(interaction.user.id),
                actor_type="owner",
                action="disable"
            )
            
            # Alert channel
            if config.alerts_channel_id:
                alert_channel = self.bot.get_channel(int(config.alerts_channel_id))
                if alert_channel:
                    embed = discord.Embed(
                        title="✅ SAFE MODE DEVRE DIŞI",
                        description="Normal operasyona dönüldü.\nOtomatik enforcement tekrar aktif.",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="Kapatan", value=interaction.user.mention, inline=True)
                    
                    await alert_channel.send(embed=embed)
        
        await interaction.followup.send(
            "✅ Safe mode deaktive edildi.\n"
            "Normal operasyona dönüldü.",
            ephemeral=True
        )
    
    @safemode.command(name="status", description="Safe mode durumunu göster")
    async def safemode_status(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            config = await governance_svc.get_or_create_config(str(interaction.guild_id))
        
        embed = discord.Embed(
            title="🛡️ Governance Durumu",
            color=discord.Color.red() if config.safe_mode_active else discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Safe Mode",
            value="🔴 AKTİF" if config.safe_mode_active else "🟢 Kapalı",
            inline=True
        )
        embed.add_field(
            name="Lockdown",
            value="🔒 AKTİF" if config.lockdown_active else "🔓 Kapalı",
            inline=True
        )
        embed.add_field(
            name="Governance Mode",
            value=config.governance_mode.upper(),
            inline=True
        )
        
        if config.safe_mode_active:
            embed.add_field(
                name="Safe Mode Başlangıç",
                value=f"<t:{int(config.safe_mode_started_at.timestamp())}:R>" if config.safe_mode_started_at else "?",
                inline=True
            )
        
        if config.lockdown_active:
            embed.add_field(
                name="Lockdown Sebebi",
                value=config.lockdown_reason or "Belirtilmedi",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ==================== LOCKDOWN ====================
    
    governance = app_commands.Group(name="governance", description="Governance komutları")
    
    @governance.command(name="lockdown", description="Lockdown'ı etkinleştir/devre dışı bırak")
    @app_commands.describe(
        action="enable veya disable",
        reason="Lockdown sebebi",
        duration="Süre (dakika cinsinden)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Etkinleştir", value="enable"),
        app_commands.Choice(name="Devre Dışı", value="disable")
    ])
    async def lockdown_cmd(
        self, 
        interaction: discord.Interaction, 
        action: str,
        reason: str = None,
        duration: int = 60
    ):
        # Permission check
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            user_roles = [str(r.id) for r in interaction.user.roles]
            
            if not (await governance_svc.is_ops_admin(str(interaction.guild_id), user_roles) or 
                    interaction.user.id == interaction.guild.owner_id):
                return await interaction.response.send_message(
                    "❌ Bu komut için OpsAdmin yetkisi gerekli!",
                    ephemeral=True
                )
        
        await interaction.response.defer()
        
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            case_svc = CaseService(db)
            
            if action == "enable":
                if not reason:
                    return await interaction.followup.send("❌ Lockdown için sebep gerekli!")
                
                config = await governance_svc.enable_lockdown(
                    str(interaction.guild_id),
                    reason,
                    duration * 60  # dakikayı saniyeye çevir
                )
                
                # Audit
                await case_svc.log_audit_event(
                    guild_id=str(interaction.guild_id),
                    event_type="lockdown",
                    actor_id=str(interaction.user.id),
                    actor_type="opsadmin",
                    action="enable",
                    details={"reason": reason, "duration_min": duration}
                )
                
                # Alert
                if config.alerts_channel_id:
                    alert_channel = self.bot.get_channel(int(config.alerts_channel_id))
                    if alert_channel:
                        embed = discord.Embed(
                            title="🔒 LOCKDOWN AKTİF",
                            description=f"**Sebep:** {reason}\n**Süre:** {duration} dakika",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="Aktive Eden", value=interaction.user.mention)
                        await alert_channel.send(embed=embed)
                
                await interaction.followup.send(
                    f"🔒 Lockdown aktive edildi.\n"
                    f"**Sebep:** {reason}\n"
                    f"**Süre:** {duration} dakika"
                )
            
            else:  # disable
                config = await governance_svc.disable_lockdown(str(interaction.guild_id))
                
                # Audit
                await case_svc.log_audit_event(
                    guild_id=str(interaction.guild_id),
                    event_type="lockdown",
                    actor_id=str(interaction.user.id),
                    actor_type="opsadmin",
                    action="disable"
                )
                
                # Alert
                if config.alerts_channel_id:
                    alert_channel = self.bot.get_channel(int(config.alerts_channel_id))
                    if alert_channel:
                        embed = discord.Embed(
                            title="🔓 LOCKDOWN KALDIRILDI",
                            description="Sunucu normal operasyona döndü.",
                            color=discord.Color.green(),
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="Kaldıran", value=interaction.user.mention)
                        await alert_channel.send(embed=embed)
                
                await interaction.followup.send("🔓 Lockdown kaldırıldı.")
    
    @governance.command(name="config", description="Governance konfigürasyonunu göster")
    async def governance_config(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            config = await governance_svc.get_or_create_config(str(interaction.guild_id))
        
        embed = discord.Embed(
            title="⚙️ Governance Konfigürasyonu",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        # Mode
        embed.add_field(name="Mode", value=config.governance_mode, inline=True)
        embed.add_field(name="Safe Mode", value="🔴 Aktif" if config.safe_mode_active else "🟢 Kapalı", inline=True)
        embed.add_field(name="Lockdown", value="🔒 Aktif" if config.lockdown_active else "🔓 Kapalı", inline=True)
        
        # Thresholds
        embed.add_field(name="Raid Eşiği", value=f"{config.raid_join_threshold}/{config.raid_window_seconds}s", inline=True)
        embed.add_field(name="Newcomer Süresi", value=f"{config.newcomer_duration_hours}h", inline=True)
        embed.add_field(name="Min Mesaj", value=str(config.newcomer_min_messages), inline=True)
        
        # Retention
        embed.add_field(name="Evidence Tutma", value=f"{config.evidence_retention_days} gün", inline=True)
        embed.add_field(name="Audit Tutma", value=f"{config.audit_retention_days} gün", inline=True)
        embed.add_field(name="Auto Slowmode", value="✅" if config.auto_slowmode_enabled else "❌", inline=True)
        
        # Channels
        channels_info = []
        if config.mod_log_channel_id:
            channels_info.append(f"Mod Log: <#{config.mod_log_channel_id}>")
        if config.alerts_channel_id:
            channels_info.append(f"Alerts: <#{config.alerts_channel_id}>")
        if channels_info:
            embed.add_field(name="Kanallar", value="\n".join(channels_info), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @governance.command(name="setup-roles", description="Governance rollerini ayarla")
    @app_commands.describe(
        opsadmin="OpsAdmin rolü",
        triage="Triage rolü",
        reviewer="Reviewer rolü",
        newcomer="Newcomer rolü",
        verified="Verified rolü"
    )
    async def setup_roles(
        self,
        interaction: discord.Interaction,
        opsadmin: discord.Role = None,
        triage: discord.Role = None,
        reviewer: discord.Role = None,
        newcomer: discord.Role = None,
        verified: discord.Role = None
    ):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                "❌ Bu komut sadece sunucu sahibi tarafından kullanılabilir!",
                ephemeral=True
            )
        
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            
            await governance_svc.setup_governance_roles(
                str(interaction.guild_id),
                opsadmin_role_id=str(opsadmin.id) if opsadmin else None,
                triage_role_id=str(triage.id) if triage else None,
                reviewer_role_id=str(reviewer.id) if reviewer else None,
                newcomer_role_id=str(newcomer.id) if newcomer else None,
                verified_role_id=str(verified.id) if verified else None
            )
        
        embed = discord.Embed(
            title="✅ Roller Ayarlandı",
            color=discord.Color.green()
        )
        if opsadmin:
            embed.add_field(name="OpsAdmin", value=opsadmin.mention, inline=True)
        if triage:
            embed.add_field(name="Triage", value=triage.mention, inline=True)
        if reviewer:
            embed.add_field(name="Reviewer", value=reviewer.mention, inline=True)
        if newcomer:
            embed.add_field(name="Newcomer", value=newcomer.mention, inline=True)
        if verified:
            embed.add_field(name="Verified", value=verified.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @governance.command(name="setup-channels", description="Governance kanallarını ayarla")
    @app_commands.describe(
        mod_log="Mod log kanalı",
        audit_log="Detaylı audit log kanalı",
        alerts="Önemli uyarılar kanalı",
        new_members="Yeni üyeler kanalı"
    )
    async def setup_channels(
        self,
        interaction: discord.Interaction,
        mod_log: discord.TextChannel = None,
        audit_log: discord.TextChannel = None,
        alerts: discord.TextChannel = None,
        new_members: discord.TextChannel = None
    ):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                "❌ Bu komut sadece sunucu sahibi tarafından kullanılabilir!",
                ephemeral=True
            )
        
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            
            await governance_svc.setup_governance_channels(
                str(interaction.guild_id),
                mod_log_channel_id=str(mod_log.id) if mod_log else None,
                audit_log_channel_id=str(audit_log.id) if audit_log else None,
                alerts_channel_id=str(alerts.id) if alerts else None,
                new_members_channel_id=str(new_members.id) if new_members else None
            )
        
        embed = discord.Embed(
            title="✅ Kanallar Ayarlandı",
            color=discord.Color.green()
        )
        if mod_log:
            embed.add_field(name="Mod Log", value=mod_log.mention, inline=True)
        if audit_log:
            embed.add_field(name="Audit Log", value=audit_log.mention, inline=True)
        if alerts:
            embed.add_field(name="Alerts", value=alerts.mention, inline=True)
        if new_members:
            embed.add_field(name="New Members", value=new_members.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SafeModeHandler(bot))
