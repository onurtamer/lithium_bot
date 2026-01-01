"""
Gelişmiş AutoMod Sistemi
- Küfür/Argo Engelleyici
- Caps Lock Koruması
- Gelişmiş Link Engelleyici
- Gelişmiş Spam Koruması
- Sesli Kanal Koruması (Mic Spam)
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import Guild
from lithium_core.models.security import (
    AutoModConfig, BadWordFilter, TempMute, VoiceSpamLog
)
from sqlalchemy import select, delete
import logging
import re
import os
import redis.asyncio as redis
from datetime import datetime, timedelta

logger = logging.getLogger("lithium-bot")


class AdvancedAutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = None
        self.voice_join_cache = {}  # {guild_id-user_id: [timestamps]}
        self.unmute_checker.start()
        
        # Varsayılan Türkçe küfür listesi
        self.default_bad_words = [
            "amk", "aq", "oç", "orospu", "piç", "sikik", "yarrak", 
            "göt", "amcık", "pezevenk", "ibne", "oğlancı", "puşt"
        ]

    async def cog_load(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis = redis.from_url(redis_url)

    def cog_unload(self):
        self.unmute_checker.cancel()

    async def get_config(self, guild_id: int) -> AutoModConfig:
        """AutoMod config al veya varsayılan oluştur"""
        async with AsyncSessionLocal() as db:
            stmt = select(AutoModConfig).where(AutoModConfig.guild_id == str(guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            if not config:
                config = AutoModConfig(guild_id=str(guild_id))
                db.add(config)
                await db.commit()
                await db.refresh(config)
            return config

    async def get_bad_words(self, guild_id: int) -> list:
        """Sunucu için yasaklı kelime listesi al"""
        async with AsyncSessionLocal() as db:
            stmt = select(BadWordFilter).where(BadWordFilter.guild_id == str(guild_id))
            words = (await db.execute(stmt)).scalars().all()
            return [w.word.lower() for w in words] if words else self.default_bad_words

    async def is_immune(self, member: discord.Member, config: AutoModConfig) -> bool:
        """Üyenin automod'dan muaf olup olmadığını kontrol et"""
        if member.guild_permissions.administrator:
            return True
        if member.guild_permissions.manage_messages:
            return True
        return False

    async def warn_user(self, message: discord.Message, reason: str):
        """Kullanıcıya uyarı ver"""
        try:
            await message.delete()
        except:
            pass
        
        warning = await message.channel.send(
            f"⚠️ {message.author.mention}, {reason}",
            delete_after=5
        )

    async def mute_user(self, member: discord.Member, duration: int, reason: str):
        """Kullanıcıyı geçici olarak sustur"""
        try:
            # Discord'un timeout özelliğini kullan
            until = discord.utils.utcnow() + timedelta(seconds=duration)
            await member.timeout(until, reason=reason)
            
            # Database'e kaydet
            async with AsyncSessionLocal() as db:
                mute = TempMute(
                    guild_id=str(member.guild.id),
                    user_id=str(member.id),
                    moderator_id=str(self.bot.user.id),
                    reason=reason,
                    unmute_at=datetime.utcnow() + timedelta(seconds=duration)
                )
                db.add(mute)
                await db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Mute failed: {e}")
            return False

    @tasks.loop(minutes=1)
    async def unmute_checker(self):
        """Süresi dolan mute'ları kaldır"""
        async with AsyncSessionLocal() as db:
            stmt = select(TempMute).where(
                TempMute.active == True,
                TempMute.unmute_at <= datetime.utcnow()
            )
            expired_mutes = (await db.execute(stmt)).scalars().all()
            
            for mute in expired_mutes:
                try:
                    guild = self.bot.get_guild(int(mute.guild_id))
                    if guild:
                        member = guild.get_member(int(mute.user_id))
                        if member and member.is_timed_out():
                            await member.timeout(None, reason="Mute süresi doldu")
                    
                    mute.active = False
                    await db.commit()
                except Exception as e:
                    logger.error(f"Unmute error: {e}")

    @unmute_checker.before_loop
    async def before_unmute_checker(self):
        await self.bot.wait_until_ready()

    # ==================== MESAJ FİLTRELERİ ====================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        
        # Guild config kontrolü
        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.id == str(message.guild.id))
            guild = (await db.execute(stmt)).scalar_one_or_none()
            if not guild or not guild.automod_enabled:
                return

        config = await self.get_config(message.guild.id)
        
        # Admin/Mod kontrolü
        if await self.is_immune(message.author, config):
            return

        # 1. KÜFÜR/ARGO FİLTRESİ
        if config.bad_words_enabled:
            bad_words = await self.get_bad_words(message.guild.id)
            content_lower = message.content.lower()
            
            for word in bad_words:
                # Kelime sınırı kontrolü ile
                pattern = rf'\b{re.escape(word)}\b'
                if re.search(pattern, content_lower):
                    await self.warn_user(message, "küfür/argo kullanımı yasaktır!")
                    return

        # 2. CAPS LOCK KORUMASI
        if config.caps_enabled:
            content = message.content
            if len(content) >= config.caps_min_length:
                uppercase_count = sum(1 for c in content if c.isupper())
                letter_count = sum(1 for c in content if c.isalpha())
                
                if letter_count > 0:
                    caps_percentage = (uppercase_count / letter_count) * 100
                    if caps_percentage >= config.caps_threshold:
                        await self.warn_user(message, "çok fazla BÜYÜK HARF kullanmayın!")
                        return

        # 3. LINK KORUMASI
        if config.link_enabled:
            # Link regex
            url_pattern = r'https?://[^\s]+'
            if re.search(url_pattern, message.content):
                # İzin verilen kanallar
                if str(message.channel.id) not in config.link_allowed_channels:
                    # İzin verilen roller
                    user_role_ids = [str(r.id) for r in message.author.roles]
                    if not any(rid in config.link_allowed_roles for rid in user_role_ids):
                        # Whitelist kontrolü
                        is_whitelisted = False
                        for domain in config.link_whitelist:
                            if domain in message.content:
                                is_whitelisted = True
                                break
                        
                        if not is_whitelisted:
                            await self.warn_user(message, "link paylaşımı yasaktır!")
                            return

        # 4. SPAM KORUMASI
        if config.spam_enabled:
            if self.redis:
                key = f"spam:{message.guild.id}:{message.author.id}"
                count = await self.redis.incr(key)
                await self.redis.expire(key, config.spam_interval)
                
                if count > config.spam_threshold:
                    try:
                        await message.delete()
                    except:
                        pass
                    
                    if config.spam_action == "MUTE":
                        success = await self.mute_user(
                            message.author, 
                            config.spam_mute_duration,
                            f"Spam koruması ({count} mesaj/{config.spam_interval}s)"
                        )
                        if success:
                            await message.channel.send(
                                f"🔇 {message.author.mention} spam nedeniyle {config.spam_mute_duration // 60} dakika susturuldu.",
                                delete_after=10
                            )
                    elif config.spam_action == "WARN":
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, çok hızlı mesaj atmayın!",
                            delete_after=5
                        )
                    return

    # ==================== SESLİ KANAL KORUMASI ====================

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Sesli kanal gir-çık spam kontrolü"""
        if member.bot:
            return

        # Sadece kanal değişikliklerini izle
        if before.channel == after.channel:
            return

        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.id == str(member.guild.id))
            guild_config = (await db.execute(stmt)).scalar_one_or_none()
            if not guild_config or not guild_config.automod_enabled:
                return

        config = await self.get_config(member.guild.id)
        
        if not config.voice_spam_enabled:
            return

        key = f"{member.guild.id}-{member.id}"
        now = datetime.utcnow()
        
        # Cache'i güncelle
        if key not in self.voice_join_cache:
            self.voice_join_cache[key] = []
        
        # Eski kayıtları temizle
        self.voice_join_cache[key] = [
            t for t in self.voice_join_cache[key] 
            if (now - t).seconds < config.voice_spam_interval
        ]
        
        # Yeni kaydı ekle
        self.voice_join_cache[key].append(now)
        
        # Threshold kontrolü
        if len(self.voice_join_cache[key]) >= config.voice_spam_threshold:
            try:
                # Kullanıcıyı sesli kanaldan at
                await member.move_to(None, reason="Sesli kanal spam koruması")
                
                # Kısa süreli mute
                await self.mute_user(member, 60, "Sesli kanal spam")
                
                # Log kaydet
                async with AsyncSessionLocal() as db:
                    log = VoiceSpamLog(
                        guild_id=str(member.guild.id),
                        user_id=str(member.id),
                        action_taken="DISCONNECT",
                        join_count=len(self.voice_join_cache[key])
                    )
                    db.add(log)
                    await db.commit()
                
                # Cache temizle
                self.voice_join_cache[key] = []
                
                logger.info(f"Voice spam protection triggered for {member} in {member.guild.name}")
            except Exception as e:
                logger.error(f"Voice spam action failed: {e}")

    # ==================== YAPILANDIRMA KOMUTLARI ====================

    @app_commands.command(name="automod_config", description="AutoMod ayarlarını görüntüle/değiştir")
    @app_commands.describe(
        caps_enabled="Caps Lock koruması",
        caps_threshold="Caps eşiği (%)",
        spam_enabled="Spam koruması",
        spam_threshold="Spam eşiği (mesaj sayısı)",
        link_enabled="Link koruması",
        bad_words_enabled="Küfür filtresi"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def automod_config(
        self, 
        interaction: discord.Interaction,
        caps_enabled: bool = None,
        caps_threshold: int = None,
        spam_enabled: bool = None,
        spam_threshold: int = None,
        link_enabled: bool = None,
        bad_words_enabled: bool = None
    ):
        async with AsyncSessionLocal() as db:
            stmt = select(AutoModConfig).where(AutoModConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                config = AutoModConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            # Güncelle
            if caps_enabled is not None:
                config.caps_enabled = caps_enabled
            if caps_threshold is not None:
                config.caps_threshold = max(50, min(100, caps_threshold))
            if spam_enabled is not None:
                config.spam_enabled = spam_enabled
            if spam_threshold is not None:
                config.spam_threshold = max(3, min(20, spam_threshold))
            if link_enabled is not None:
                config.link_enabled = link_enabled
            if bad_words_enabled is not None:
                config.bad_words_enabled = bad_words_enabled
            
            await db.commit()
            await db.refresh(config)

        # Mevcut ayarları göster
        embed = discord.Embed(
            title="🛡️ AutoMod Ayarları",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Caps Lock Koruması",
            value=f"{'✅ Aktif' if config.caps_enabled else '❌ Kapalı'} (Eşik: %{config.caps_threshold})",
            inline=True
        )
        embed.add_field(
            name="Spam Koruması",
            value=f"{'✅ Aktif' if config.spam_enabled else '❌ Kapalı'} ({config.spam_threshold} msg/{config.spam_interval}s)",
            inline=True
        )
        embed.add_field(
            name="Link Koruması",
            value=f"{'✅ Aktif' if config.link_enabled else '❌ Kapalı'}",
            inline=True
        )
        embed.add_field(
            name="Küfür Filtresi",
            value=f"{'✅ Aktif' if config.bad_words_enabled else '❌ Kapalı'}",
            inline=True
        )
        embed.add_field(
            name="Ses Spam Koruması",
            value=f"{'✅ Aktif' if config.voice_spam_enabled else '❌ Kapalı'}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="badword_add", description="Yasaklı kelime ekle")
    @app_commands.checks.has_permissions(administrator=True)
    async def badword_add(self, interaction: discord.Interaction, word: str, severity: str = "WARN"):
        """Yasaklı kelime ekle"""
        async with AsyncSessionLocal() as db:
            filter_word = BadWordFilter(
                guild_id=str(interaction.guild_id),
                word=word.lower(),
                severity=severity.upper()
            )
            db.add(filter_word)
            await db.commit()
        
        await interaction.response.send_message(
            f"✅ `{word}` yasaklı kelime listesine eklendi. (Eylem: {severity})",
            ephemeral=True
        )

    @app_commands.command(name="badword_remove", description="Yasaklı kelime kaldır")
    @app_commands.checks.has_permissions(administrator=True)
    async def badword_remove(self, interaction: discord.Interaction, word: str):
        """Yasaklı kelime kaldır"""
        async with AsyncSessionLocal() as db:
            stmt = delete(BadWordFilter).where(
                BadWordFilter.guild_id == str(interaction.guild_id),
                BadWordFilter.word == word.lower()
            )
            result = await db.execute(stmt)
            await db.commit()
        
        if result.rowcount > 0:
            await interaction.response.send_message(f"✅ `{word}` yasaklı kelime listesinden kaldırıldı.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ `{word}` listede bulunamadı.", ephemeral=True)

    @app_commands.command(name="badword_list", description="Yasaklı kelimeleri listele")
    @app_commands.checks.has_permissions(administrator=True)
    async def badword_list(self, interaction: discord.Interaction):
        """Yasaklı kelimeleri listele"""
        async with AsyncSessionLocal() as db:
            stmt = select(BadWordFilter).where(BadWordFilter.guild_id == str(interaction.guild_id))
            words = (await db.execute(stmt)).scalars().all()
        
        if not words:
            # Varsayılan listeyi göster
            word_list = ", ".join([f"`{w}`" for w in self.default_bad_words[:10]])
            return await interaction.response.send_message(
                f"📋 Özel liste yok. Varsayılan liste kullanılıyor:\n{word_list}...",
                ephemeral=True
            )
        
        word_list = ", ".join([f"`{w.word}`" for w in words[:30]])
        await interaction.response.send_message(
            f"📋 Yasaklı Kelimeler ({len(words)} adet):\n{word_list}",
            ephemeral=True
        )

    @app_commands.command(name="link_whitelist", description="Link whitelist'e domain ekle")
    @app_commands.checks.has_permissions(administrator=True)
    async def link_whitelist(self, interaction: discord.Interaction, domain: str):
        """Link whitelist'e domain ekle"""
        async with AsyncSessionLocal() as db:
            stmt = select(AutoModConfig).where(AutoModConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                config = AutoModConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            whitelist = list(config.link_whitelist) if config.link_whitelist else []
            if domain not in whitelist:
                whitelist.append(domain)
                config.link_whitelist = whitelist
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(config, "link_whitelist")
                
                await db.commit()
        
        await interaction.response.send_message(
            f"✅ `{domain}` link whitelist'e eklendi.",
            ephemeral=True
        )

    @app_commands.command(name="link_allow_role", description="Bir role link atma izni ver")
    @app_commands.checks.has_permissions(administrator=True)
    async def link_allow_role(self, interaction: discord.Interaction, role: discord.Role):
        """Bir role link atma izni ver"""
        async with AsyncSessionLocal() as db:
            stmt = select(AutoModConfig).where(AutoModConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                config = AutoModConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            allowed = list(config.link_allowed_roles) if config.link_allowed_roles else []
            if str(role.id) not in allowed:
                allowed.append(str(role.id))
                config.link_allowed_roles = allowed
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(config, "link_allowed_roles")
                
                await db.commit()
        
        await interaction.response.send_message(
            f"✅ {role.mention} artık link atabilir.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(AdvancedAutoMod(bot))
