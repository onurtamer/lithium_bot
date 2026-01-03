"""
Gelişmiş Audit Logging Cog
- Silinen/düzenlenen mesajlar
- Sesli kanal giriş-çıkışları
- Rol değişiklikleri
- Üye güncellemeleri
"""
import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import LogRoute, Guild, AuditLog
from sqlalchemy import select
from datetime import datetime
import logging

logger = logging.getLogger("lithium-bot")


class AuditLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild_id: int, module: str) -> discord.TextChannel:
        """Log kanalını al"""
        async with AsyncSessionLocal() as db:
            stmt = select(LogRoute).where(
                LogRoute.guild_id == str(guild_id),
                LogRoute.module == module.upper()
            )
            route = (await db.execute(stmt)).scalar_one_or_none()
            if route:
                return self.bot.get_channel(int(route.channel_id))
        return None

    async def is_logging_enabled(self, guild_id: int) -> bool:
        """Loglama aktif mi kontrol et"""
        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.discord_id == str(guild_id))
            guild = (await db.execute(stmt)).scalar_one_or_none()
            return guild.logs_enabled if guild else False

    async def save_audit_log(self, guild_id: str, user_id: str, action: str, target: str, changes: dict = None):
        """Audit log kaydet"""
        async with AsyncSessionLocal() as db:
            log = AuditLog(
                guild_id=guild_id,
                user_id=user_id,
                action=action,
                target=target,
                changes=changes
            )
            db.add(log)
            await db.commit()

    # ==================== MESAJ LOGLAR ====================
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Silinen mesajları logla"""
        if not message.guild or message.author.bot:
            return
        
        if not await self.is_logging_enabled(message.guild.id):
            return

        channel = await self.get_log_channel(message.guild.id, "MESSAGES")
        if not channel:
            return

        embed = discord.Embed(
            title="🗑️ Mesaj Silindi",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
        embed.add_field(name="Yazar", value=f"{message.author.mention} ({message.author.id})", inline=True)
        
        content = message.content[:1000] if message.content else "*İçerik yok*"
        embed.add_field(name="İçerik", value=f"```{content}```", inline=False)
        
        if message.attachments:
            embed.add_field(name="Ekler", value=", ".join([a.filename for a in message.attachments]), inline=False)
        
        embed.set_footer(text=f"Mesaj ID: {message.id}")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        
        await channel.send(embed=embed)
        await self.save_audit_log(str(message.guild.id), str(message.author.id), "MESSAGE_DELETE", str(message.channel.id))

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Düzenlenen mesajları logla"""
        if not before.guild or before.author.bot:
            return
        
        if before.content == after.content:
            return
        
        if not await self.is_logging_enabled(before.guild.id):
            return

        channel = await self.get_log_channel(before.guild.id, "MESSAGES")
        if not channel:
            return

        embed = discord.Embed(
            title="✏️ Mesaj Düzenlendi",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="Yazar", value=f"{before.author.mention}", inline=True)
        embed.add_field(name="Mesaja Git", value=f"[Tıkla]({after.jump_url})", inline=True)
        
        old_content = before.content[:500] if before.content else "*Boş*"
        new_content = after.content[:500] if after.content else "*Boş*"
        
        embed.add_field(name="Eski İçerik", value=f"```{old_content}```", inline=False)
        embed.add_field(name="Yeni İçerik", value=f"```{new_content}```", inline=False)
        
        embed.set_thumbnail(url=before.author.display_avatar.url)
        
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list):
        """Toplu silinen mesajları logla"""
        if not messages:
            return
        
        message = messages[0]
        if not message.guild:
            return
        
        if not await self.is_logging_enabled(message.guild.id):
            return

        channel = await self.get_log_channel(message.guild.id, "MESSAGES")
        if not channel:
            return

        embed = discord.Embed(
            title="🗑️ Toplu Mesaj Silindi",
            description=f"**{len(messages)}** mesaj silindi",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
        
        await channel.send(embed=embed)

    # ==================== SES LOGLAR ====================
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Sesli kanal giriş-çıkışları logla"""
        if member.bot:
            return
        
        if not await self.is_logging_enabled(member.guild.id):
            return

        channel = await self.get_log_channel(member.guild.id, "VOICE")
        if not channel:
            return

        embed = None
        
        # Sesli kanala katıldı
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🔊 Sesli Kanala Katıldı",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
            embed.add_field(name="Kanal", value=f"🔊 {after.channel.name}", inline=True)
        
        # Sesli kanaldan ayrıldı
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 Sesli Kanaldan Ayrıldı",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
            embed.add_field(name="Kanal", value=f"🔊 {before.channel.name}", inline=True)
        
        # Kanal değiştirdi
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="🔀 Sesli Kanal Değiştirdi",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
            embed.add_field(name="Önceki", value=f"🔊 {before.channel.name}", inline=True)
            embed.add_field(name="Şimdiki", value=f"🔊 {after.channel.name}", inline=True)
        
        # Mute/Deaf durumu değişti
        elif before.self_mute != after.self_mute or before.self_deaf != after.self_deaf:
            status = []
            if after.self_mute:
                status.append("🔇 Susturuldu")
            if after.self_deaf:
                status.append("🔈 Sağır")
            if not status:
                status.append("🔊 Normal")
            
            embed = discord.Embed(
                title="🎤 Ses Durumu Değişti",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{member.mention}", inline=True)
            embed.add_field(name="Durum", value=" | ".join(status), inline=True)
        
        if embed:
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    # ==================== ÜYE LOGLAR ====================
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Üye güncellemelerini logla (rol değişiklikleri vb.)"""
        if before.bot:
            return
        
        if not await self.is_logging_enabled(before.guild.id):
            return

        channel = await self.get_log_channel(before.guild.id, "MEMBERS")
        if not channel:
            return

        # Rol değişikliği
        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="🎭 Rol Değişikliği",
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Üye", value=f"{after.mention} ({after.id})", inline=False)
                
                if added_roles:
                    roles_str = ", ".join([r.mention for r in added_roles])
                    embed.add_field(name="➕ Eklenen Roller", value=roles_str, inline=False)
                
                if removed_roles:
                    roles_str = ", ".join([r.mention for r in removed_roles])
                    embed.add_field(name="➖ Kaldırılan Roller", value=roles_str, inline=False)
                
                embed.set_thumbnail(url=after.display_avatar.url)
                await channel.send(embed=embed)
        
        # Takma ad değişikliği
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Takma Ad Değişikliği",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Üye", value=f"{after.mention}", inline=True)
            embed.add_field(name="Önceki", value=before.nick or "*Yok*", inline=True)
            embed.add_field(name="Yeni", value=after.nick or "*Yok*", inline=True)
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Yasaklanan üyeleri logla"""
        if not await self.is_logging_enabled(guild.id):
            return

        channel = await self.get_log_channel(guild.id, "MODERATION")
        if not channel:
            return

        embed = discord.Embed(
            title="🔨 Üye Yasaklandı",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Kullanıcı", value=f"{user.mention} ({user.id})", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Audit log'dan ban sebebini almaya çalış
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed.add_field(name="Moderatör", value=f"{entry.user.mention}", inline=True)
                    embed.add_field(name="Sebep", value=entry.reason or "Sebep belirtilmedi", inline=True)
                    break
        except:
            pass
        
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Yasağı kaldırılan üyeleri logla"""
        if not await self.is_logging_enabled(guild.id):
            return

        channel = await self.get_log_channel(guild.id, "MODERATION")
        if not channel:
            return

        embed = discord.Embed(
            title="✅ Yasak Kaldırıldı",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Kullanıcı", value=f"{user.mention} ({user.id})", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await channel.send(embed=embed)

    # ==================== LOG SETUP KOMUTLARI ====================
    
    @app_commands.command(name="log_setup", description="Log kanalını ayarla")
    @app_commands.describe(
        module="Log türü",
        channel="Log kanalı"
    )
    @app_commands.choices(module=[
        app_commands.Choice(name="Mesajlar (Silme/Düzenleme)", value="MESSAGES"),
        app_commands.Choice(name="Sesli Kanallar", value="VOICE"),
        app_commands.Choice(name="Üye Değişiklikleri", value="MEMBERS"),
        app_commands.Choice(name="Moderasyon", value="MODERATION"),
        app_commands.Choice(name="Sunucu", value="SERVER"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def log_setup(self, interaction: discord.Interaction, module: str, channel: discord.TextChannel):
        async with AsyncSessionLocal() as db:
            stmt = select(LogRoute).where(
                LogRoute.guild_id == str(interaction.guild_id),
                LogRoute.module == module
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            
            if existing:
                existing.channel_id = str(channel.id)
            else:
                route = LogRoute(
                    guild_id=str(interaction.guild_id),
                    module=module,
                    channel_id=str(channel.id)
                )
                db.add(route)
            
            await db.commit()
        
        module_names = {
            "MESSAGES": "Mesaj Logları",
            "VOICE": "Ses Logları",
            "MEMBERS": "Üye Logları",
            "MODERATION": "Moderasyon Logları",
            "SERVER": "Sunucu Logları"
        }
        
        await interaction.response.send_message(
            f"✅ **{module_names.get(module, module)}** artık {channel.mention} kanalına gönderilecek.",
            ephemeral=True
        )

    @app_commands.command(name="log_list", description="Aktif log kanallarını göster")
    @app_commands.checks.has_permissions(administrator=True)
    async def log_list(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            stmt = select(LogRoute).where(LogRoute.guild_id == str(interaction.guild_id))
            routes = (await db.execute(stmt)).scalars().all()
        
        if not routes:
            return await interaction.response.send_message("❌ Hiç log kanalı ayarlanmamış.", ephemeral=True)
        
        embed = discord.Embed(
            title="📋 Aktif Log Kanalları",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        for route in routes:
            channel = self.bot.get_channel(int(route.channel_id))
            channel_mention = channel.mention if channel else f"#{route.channel_id} (bulunamadı)"
            embed.add_field(name=route.module, value=channel_mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AuditLogging(bot))
