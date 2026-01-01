"""
Jail (Hapis) ve Gelişmiş Mute Sistemi
- Jail (Hapis) sistemi - tek kanal görebilen özel rol
- Süreli susturma (Temp Mute)
- Unjail/Unmute komutları
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.security import JailConfig, JailedUser, TempMute
from sqlalchemy import select, delete
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger("lithium-bot")


def parse_duration(duration_str: str) -> int:
    """Süre string'ini saniyeye çevir (örn: 10m, 1h, 1d)"""
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        return None
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    return amount * multipliers.get(unit, 60)


class JailSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jail_checker.start()

    def cog_unload(self):
        self.jail_checker.cancel()

    @tasks.loop(minutes=1)
    async def jail_checker(self):
        """Süresi dolan jail'leri kontrol et"""
        async with AsyncSessionLocal() as db:
            stmt = select(JailedUser).where(
                JailedUser.release_at != None,
                JailedUser.release_at <= datetime.utcnow()
            )
            expired = (await db.execute(stmt)).scalars().all()
            
            for jailed in expired:
                try:
                    guild = self.bot.get_guild(int(jailed.guild_id))
                    if not guild:
                        continue
                    
                    member = guild.get_member(int(jailed.user_id))
                    if not member:
                        continue
                    
                    # Config al
                    config_stmt = select(JailConfig).where(JailConfig.guild_id == jailed.guild_id)
                    config = (await db.execute(config_stmt)).scalar_one_or_none()
                    if not config:
                        continue
                    
                    # Jail rolünü kaldır
                    jail_role = guild.get_role(int(config.jail_role_id))
                    if jail_role and jail_role in member.roles:
                        await member.remove_roles(jail_role, reason="Hapis süresi doldu")
                    
                    # Eski rolleri geri ver
                    if jailed.previous_roles:
                        for role_id in jailed.previous_roles:
                            role = guild.get_role(int(role_id))
                            if role and role not in member.roles:
                                try:
                                    await member.add_roles(role, reason="Hapis süresi doldu - roller geri verildi")
                                except:
                                    pass
                    
                    # Kayıt sil
                    await db.delete(jailed)
                    await db.commit()
                    
                    logger.info(f"Auto-unjailed {member} in {guild.name}")
                except Exception as e:
                    logger.error(f"Jail checker error: {e}")

    @jail_checker.before_loop
    async def before_jail_checker(self):
        await self.bot.wait_until_ready()

    # ==================== JAIL SETUP ====================

    @app_commands.command(name="jail_setup", description="Jail sistemini kur")
    @app_commands.describe(
        jail_role="Hapis rolü (tüm kanallardan gizlenecek)",
        jail_channel="Hapis kanalı (sadece bu kanalı görecekler)",
        log_channel="Log kanalı (opsiyonel)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def jail_setup(
        self, 
        interaction: discord.Interaction, 
        jail_role: discord.Role,
        jail_channel: discord.TextChannel,
        log_channel: discord.TextChannel = None
    ):
        await interaction.response.defer(ephemeral=True)
        
        # Kanal izinlerini ayarla
        try:
            # Tüm kanallarda jail rolünü gizle
            for channel in interaction.guild.channels:
                try:
                    await channel.set_permissions(jail_role, read_messages=False, send_messages=False)
                except:
                    pass
            
            # Jail kanalında sadece jail rolüne izin ver
            await jail_channel.set_permissions(jail_role, read_messages=True, send_messages=True)
            await jail_channel.set_permissions(interaction.guild.default_role, read_messages=False)
            
        except discord.Forbidden:
            return await interaction.followup.send("❌ İzin ayarlama yetkisi yok!", ephemeral=True)

        # Config kaydet
        async with AsyncSessionLocal() as db:
            stmt = select(JailConfig).where(JailConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                config = JailConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.jail_role_id = str(jail_role.id)
            config.jail_channel_id = str(jail_channel.id)
            if log_channel:
                config.log_channel_id = str(log_channel.id)
            
            await db.commit()

        embed = discord.Embed(
            title="✅ Jail Sistemi Kuruldu",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Hapis Rolü", value=jail_role.mention, inline=True)
        embed.add_field(name="Hapis Kanalı", value=jail_channel.mention, inline=True)
        if log_channel:
            embed.add_field(name="Log Kanalı", value=log_channel.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ==================== JAIL KOMUTLARI ====================

    @app_commands.command(name="jail", description="Bir üyeyi hapise at")
    @app_commands.describe(
        member="Hapse atılacak üye",
        reason="Sebep",
        duration="Süre (örn: 1h, 30m, 1d) - boş bırakılırsa süresiz"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def jail(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: str = "Sebep belirtilmedi",
        duration: str = None
    ):
        # Kontroller
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendinizi hapse atamazsınız!", ephemeral=True)
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Sizden yüksek veya eşit roldeki birini hapse atamazsınız!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Botları hapse atamazsınız!", ephemeral=True)

        await interaction.response.defer()

        # Config kontrol
        async with AsyncSessionLocal() as db:
            stmt = select(JailConfig).where(JailConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                return await interaction.followup.send("❌ Jail sistemi kurulmamış! `/jail_setup` kullanın.")
            
            jail_role = interaction.guild.get_role(int(config.jail_role_id))
            if not jail_role:
                return await interaction.followup.send("❌ Jail rolü bulunamadı!")
            
            # Zaten hapiste mi?
            existing = await db.execute(
                select(JailedUser).where(
                    JailedUser.guild_id == str(interaction.guild_id),
                    JailedUser.user_id == str(member.id)
                )
            )
            if existing.scalar_one_or_none():
                return await interaction.followup.send(f"❌ {member.mention} zaten hapiste!")

            # Süre hesapla
            release_at = None
            if duration:
                seconds = parse_duration(duration)
                if seconds:
                    release_at = datetime.utcnow() + timedelta(seconds=seconds)

            # Mevcut rolleri kaydet
            previous_roles = [str(r.id) for r in member.roles if r != interaction.guild.default_role and r.is_assignable()]
            
            # Rolleri kaldır ve jail rolü ver
            try:
                roles_to_remove = [r for r in member.roles if r != interaction.guild.default_role and r.is_assignable()]
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason=f"Jail: {reason}")
                await member.add_roles(jail_role, reason=f"Jail: {reason}")
            except discord.Forbidden:
                return await interaction.followup.send("❌ Rol değiştirme yetkisi yok!")

            # Database kaydet
            jailed = JailedUser(
                guild_id=str(interaction.guild_id),
                user_id=str(member.id),
                jailed_by=str(interaction.user.id),
                reason=reason,
                previous_roles=previous_roles,
                release_at=release_at
            )
            db.add(jailed)
            await db.commit()

        # Embed oluştur
        embed = discord.Embed(
            title="🔒 Üye Hapse Atıldı",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Üye", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Moderatör", value=interaction.user.mention, inline=True)
        embed.add_field(name="Sebep", value=reason, inline=False)
        
        if release_at:
            embed.add_field(name="Süre", value=f"<t:{int(release_at.timestamp())}:R>", inline=True)
        else:
            embed.add_field(name="Süre", value="♾️ Süresiz", inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

        # Jail kanalına bilgilendirme
        jail_channel = interaction.guild.get_channel(int(config.jail_channel_id))
        if jail_channel:
            info_embed = discord.Embed(
                title="⚠️ Hapse Atıldınız",
                description=f"**Sebep:** {reason}\n\nBuradan çıkmak için özür dilemeniz ve moderatörlerin sizi serbest bırakması gerekiyor.",
                color=discord.Color.red()
            )
            if release_at:
                info_embed.add_field(name="Otomatik Çıkış", value=f"<t:{int(release_at.timestamp())}:R>")
            await jail_channel.send(f"{member.mention}", embed=info_embed)

        # Log
        if config.log_channel_id:
            log_channel = interaction.guild.get_channel(int(config.log_channel_id))
            if log_channel:
                await log_channel.send(embed=embed)

    @app_commands.command(name="unjail", description="Bir üyeyi hapisten çıkar")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unjail(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Serbest bırakıldı"):
        await interaction.response.defer()

        async with AsyncSessionLocal() as db:
            # Config al
            config_stmt = select(JailConfig).where(JailConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(config_stmt)).scalar_one_or_none()
            
            if not config:
                return await interaction.followup.send("❌ Jail sistemi kurulmamış!")
            
            # Jailed kaydını bul
            stmt = select(JailedUser).where(
                JailedUser.guild_id == str(interaction.guild_id),
                JailedUser.user_id == str(member.id)
            )
            jailed = (await db.execute(stmt)).scalar_one_or_none()
            
            if not jailed:
                return await interaction.followup.send(f"❌ {member.mention} hapiste değil!")
            
            # Jail rolünü kaldır
            jail_role = interaction.guild.get_role(int(config.jail_role_id))
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role, reason=reason)
            
            # Eski rolleri geri ver
            if jailed.previous_roles:
                roles_to_add = []
                for role_id in jailed.previous_roles:
                    role = interaction.guild.get_role(int(role_id))
                    if role and role not in member.roles:
                        roles_to_add.append(role)
                
                if roles_to_add:
                    await member.add_roles(*roles_to_add, reason="Hapisten çıkarıldı - roller geri verildi")
            
            # Kayıt sil
            await db.delete(jailed)
            await db.commit()

        embed = discord.Embed(
            title="🔓 Üye Hapisten Çıkarıldı",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
        embed.add_field(name="Moderatör", value=interaction.user.mention, inline=True)
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="jaillist", description="Hapisteki üyeleri listele")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def jaillist(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            stmt = select(JailedUser).where(JailedUser.guild_id == str(interaction.guild_id))
            jailed_users = (await db.execute(stmt)).scalars().all()
        
        if not jailed_users:
            return await interaction.response.send_message("✅ Hapiste kimse yok!", ephemeral=True)
        
        embed = discord.Embed(
            title="🔒 Hapisteki Üyeler",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        
        for jailed in jailed_users[:25]:
            member = interaction.guild.get_member(int(jailed.user_id))
            name = member.display_name if member else f"ID: {jailed.user_id}"
            
            value = f"**Sebep:** {jailed.reason[:50]}\n"
            if jailed.release_at:
                value += f"**Çıkış:** <t:{int(jailed.release_at.timestamp())}:R>"
            else:
                value += "**Süre:** ♾️ Süresiz"
            
            embed.add_field(name=name, value=value, inline=True)
        
        embed.set_footer(text=f"Toplam: {len(jailed_users)} üye")
        await interaction.response.send_message(embed=embed)

    # ==================== MUTE KOMUTLARI ====================

    @app_commands.command(name="mute", description="Bir üyeyi geçici olarak sustur")
    @app_commands.describe(
        member="Susturulacak üye",
        duration="Süre (örn: 10m, 1h, 1d)",
        reason="Sebep"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        duration: str,
        reason: str = "Sebep belirtilmedi"
    ):
        # Kontroller
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendinizi susturamazsınız!", ephemeral=True)
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Sizden yüksek veya eşit roldeki birini susturamazsınız!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Botları susturamazsınız!", ephemeral=True)

        # Süre hesapla
        seconds = parse_duration(duration)
        if not seconds:
            return await interaction.response.send_message("❌ Geçersiz süre formatı! Örnek: 10m, 1h, 1d", ephemeral=True)
        
        if seconds > 2419200:  # 28 gün
            return await interaction.response.send_message("❌ Maksimum mute süresi 28 gündür!", ephemeral=True)

        await interaction.response.defer()

        try:
            # Discord timeout kullan
            until = discord.utils.utcnow() + timedelta(seconds=seconds)
            await member.timeout(until, reason=f"{interaction.user}: {reason}")
            
            # Database kaydet
            async with AsyncSessionLocal() as db:
                mute = TempMute(
                    guild_id=str(interaction.guild_id),
                    user_id=str(member.id),
                    moderator_id=str(interaction.user.id),
                    reason=reason,
                    unmute_at=datetime.utcnow() + timedelta(seconds=seconds)
                )
                db.add(mute)
                await db.commit()
            
            embed = discord.Embed(
                title="🔇 Üye Susturuldu",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
            embed.add_field(name="Moderatör", value=interaction.user.mention, inline=True)
            embed.add_field(name="Süre", value=f"<t:{int(until.timestamp())}:R>", inline=True)
            embed.add_field(name="Sebep", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Bu üyeyi susturma yetkim yok!")
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

    @app_commands.command(name="unmute", description="Bir üyenin susturmasını kaldır")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Susturma kaldırıldı"):
        if not member.is_timed_out():
            return await interaction.response.send_message(f"❌ {member.mention} susturulmuş değil!", ephemeral=True)

        await interaction.response.defer()

        try:
            await member.timeout(None, reason=f"{interaction.user}: {reason}")
            
            # Database güncelle
            async with AsyncSessionLocal() as db:
                stmt = select(TempMute).where(
                    TempMute.guild_id == str(interaction.guild_id),
                    TempMute.user_id == str(member.id),
                    TempMute.active == True
                )
                mutes = (await db.execute(stmt)).scalars().all()
                for mute in mutes:
                    mute.active = False
                await db.commit()
            
            embed = discord.Embed(
                title="🔊 Susturma Kaldırıldı",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
            embed.add_field(name="Moderatör", value=interaction.user.mention, inline=True)
            embed.add_field(name="Sebep", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Bu üyenin susturmasını kaldırma yetkim yok!")


async def setup(bot):
    await bot.add_cog(JailSystem(bot))
