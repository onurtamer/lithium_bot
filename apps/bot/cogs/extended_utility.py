"""
Gelişmiş Utility Komutları
- Kullanıcı Bilgi Kartı (User Info)
- Avatar Getirici
- Sunucu Bilgisi
- Hava Durumu
- Döviz Kuru
- Çeviri
- Sunucu İstatistikleri
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import Guild
from sqlalchemy import select
import logging
import aiohttp
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger("lithium-bot")


class ExtendedUtility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    # ==================== KULLANICI BİLGİ KARTI ====================

    @app_commands.command(name="userinfo", description="Kullanıcı hakkında detaylı bilgi")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        # Hesap yaşı
        created_days = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
        joined_days = (datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days if member.joined_at else 0
        
        # Roller
        roles = [r.mention for r in sorted(member.roles[1:], key=lambda r: r.position, reverse=True)][:10]
        roles_str = ", ".join(roles) if roles else "Rol yok"
        
        # Badge'ler
        badges = []
        if member.public_flags.hypesquad_bravery:
            badges.append("🏠 HypeSquad Bravery")
        if member.public_flags.hypesquad_brilliance:
            badges.append("🏠 HypeSquad Brilliance")
        if member.public_flags.hypesquad_balance:
            badges.append("🏠 HypeSquad Balance")
        if member.public_flags.early_supporter:
            badges.append("💎 Early Supporter")
        if member.public_flags.verified_bot_developer:
            badges.append("🔧 Bot Developer")
        if member.public_flags.active_developer:
            badges.append("💻 Active Developer")
        if member.premium_since:
            badges.append("💜 Server Booster")
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        # Temel bilgiler
        embed.add_field(name="🏷️ Kullanıcı Adı", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="🆔 ID", value=str(member.id), inline=True)
        embed.add_field(name="🤖 Bot", value="Evet" if member.bot else "Hayır", inline=True)
        
        # Tarihler
        embed.add_field(
            name="📅 Hesap Açılış",
            value=f"<t:{int(member.created_at.timestamp())}:D>\n({created_days} gün önce)",
            inline=True
        )
        if member.joined_at:
            embed.add_field(
                name="📥 Sunucuya Katılım",
                value=f"<t:{int(member.joined_at.timestamp())}:D>\n({joined_days} gün önce)",
                inline=True
            )
        
        # Durum
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        embed.add_field(
            name="📊 Durum",
            value=f"{status_emoji.get(member.status, '⚫')} {str(member.status).title()}",
            inline=True
        )
        
        # Roller
        embed.add_field(name=f"🎭 Roller ({len(member.roles) - 1})", value=roles_str, inline=False)
        
        # Badge'ler
        if badges:
            embed.add_field(name="🏅 Rozetler", value="\n".join(badges), inline=False)
        
        # Aktivite
        if member.activities:
            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    embed.add_field(
                        name="🎵 Spotify",
                        value=f"**{activity.title}**\n{activity.artist}",
                        inline=True
                    )
                elif isinstance(activity, discord.Game):
                    embed.add_field(name="🎮 Oyun", value=activity.name, inline=True)
                elif isinstance(activity, discord.CustomActivity):
                    if activity.name:
                        embed.add_field(name="💭 Durum", value=activity.name, inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Banner (varsa)
        try:
            user = await self.bot.fetch_user(member.id)
            if user.banner:
                embed.set_image(url=user.banner.url)
        except:
            pass
        
        await interaction.response.send_message(embed=embed)

    # ==================== AVATAR GETİRİCİ ====================

    @app_commands.command(name="avatar", description="Kullanıcının avatarını getir")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'in Avatarı",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple()
        )
        
        avatar_url = member.display_avatar.url
        
        # Format linkleri
        formats = []
        for fmt in ["png", "jpg", "webp"]:
            url = member.display_avatar.with_format(fmt).url
            formats.append(f"[{fmt.upper()}]({url})")
        
        if member.display_avatar.is_animated():
            formats.append(f"[GIF]({member.display_avatar.with_format('gif').url})")
        
        embed.add_field(name="📥 İndir", value=" | ".join(formats), inline=False)
        embed.set_image(url=avatar_url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="banner", description="Kullanıcının banner'ını getir")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        try:
            user = await self.bot.fetch_user(member.id)
            if not user.banner:
                return await interaction.response.send_message("❌ Bu kullanıcının banner'ı yok!", ephemeral=True)
            
            embed = discord.Embed(
                title=f"🎨 {member.display_name}'in Banner'ı",
                color=member.color
            )
            embed.set_image(url=user.banner.url)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

    # ==================== SUNUCU BİLGİSİ ====================

    @app_commands.command(name="serverinfo", description="Sunucu hakkında detaylı bilgi")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # İstatistikler
        total_members = guild.member_count
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.add_field(name="🆔 ID", value=str(guild.id), inline=True)
        embed.add_field(name="👑 Sahip", value=f"{guild.owner.mention}" if guild.owner else "Bilinmiyor", inline=True)
        embed.add_field(
            name="📅 Oluşturulma",
            value=f"<t:{int(guild.created_at.timestamp())}:D>",
            inline=True
        )
        
        embed.add_field(
            name=f"👥 Üyeler ({total_members})",
            value=f"👤 {humans} İnsan\n🤖 {bots} Bot\n🟢 {online} Çevrimiçi",
            inline=True
        )
        embed.add_field(
            name=f"💬 Kanallar ({text_channels + voice_channels})",
            value=f"📝 {text_channels} Metin\n🔊 {voice_channels} Ses\n📁 {categories} Kategori",
            inline=True
        )
        embed.add_field(
            name="🎭 Roller",
            value=str(len(guild.roles) - 1),
            inline=True
        )
        
        # Boost bilgisi
        if guild.premium_subscription_count:
            embed.add_field(
                name="💎 Boost",
                value=f"Seviye {guild.premium_tier}\n{guild.premium_subscription_count} Boost",
                inline=True
            )
        
        # Emojiler
        if guild.emojis:
            embed.add_field(
                name="😀 Emojiler",
                value=f"{len(guild.emojis)} / {guild.emoji_limit}",
                inline=True
            )
        
        # Güvenlik
        verification = str(guild.verification_level).replace("_", " ").title()
        embed.add_field(name="🔒 Doğrulama", value=verification, inline=True)
        
        await interaction.response.send_message(embed=embed)

    # ==================== HAVA DURUMU ====================

    @app_commands.command(name="weather", description="Bir şehrin hava durumunu göster")
    @app_commands.describe(city="Şehir adı")
    async def weather(self, interaction: discord.Interaction, city: str):
        api_key = os.getenv("OPENWEATHER_API_KEY")
        
        if not api_key:
            return await interaction.response.send_message(
                "❌ Hava durumu API'si yapılandırılmamış!",
                ephemeral=True
            )
        
        await interaction.response.defer()
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=tr"
            
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send("❌ Şehir bulunamadı!")
                
                data = await resp.json()
            
            # Emoji mapping
            weather_emojis = {
                "Clear": "☀️",
                "Clouds": "☁️",
                "Rain": "🌧️",
                "Drizzle": "🌦️",
                "Thunderstorm": "⛈️",
                "Snow": "❄️",
                "Mist": "🌫️",
                "Fog": "🌫️"
            }
            
            main = data["weather"][0]["main"]
            emoji = weather_emojis.get(main, "🌍")
            
            embed = discord.Embed(
                title=f"{emoji} {data['name']}, {data['sys']['country']}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="🌡️ Sıcaklık", value=f"{data['main']['temp']:.1f}°C", inline=True)
            embed.add_field(name="🤒 Hissedilen", value=f"{data['main']['feels_like']:.1f}°C", inline=True)
            embed.add_field(name="💧 Nem", value=f"{data['main']['humidity']}%", inline=True)
            embed.add_field(name="🌬️ Rüzgar", value=f"{data['wind']['speed']} m/s", inline=True)
            embed.add_field(name="☁️ Durum", value=data["weather"][0]["description"].title(), inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

    # ==================== DÖVİZ KURU ====================

    @app_commands.command(name="currency", description="Döviz kurunu göster")
    @app_commands.describe(amount="Miktar", from_currency="Kaynak para birimi", to_currency="Hedef para birimi")
    async def currency(
        self, 
        interaction: discord.Interaction, 
        amount: float = 1.0,
        from_currency: str = "USD",
        to_currency: str = "TRY"
    ):
        await interaction.response.defer()
        
        try:
            # Ücretsiz API kullan
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
            
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send("❌ Geçersiz para birimi!")
                
                data = await resp.json()
            
            rate = data["rates"].get(to_currency.upper())
            if not rate:
                return await interaction.followup.send("❌ Hedef para birimi bulunamadı!")
            
            result = amount * rate
            
            embed = discord.Embed(
                title="💱 Döviz Çevirici",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Kaynak",
                value=f"**{amount:,.2f}** {from_currency.upper()}",
                inline=True
            )
            embed.add_field(
                name="Hedef",
                value=f"**{result:,.2f}** {to_currency.upper()}",
                inline=True
            )
            embed.add_field(
                name="Kur",
                value=f"1 {from_currency.upper()} = {rate:,.4f} {to_currency.upper()}",
                inline=False
            )
            embed.set_footer(text=f"Son güncelleme: {data['date']}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

    @app_commands.command(name="dolar", description="Dolar/TL kurunu göster")
    async def dolar(self, interaction: discord.Interaction):
        await self.currency.callback(self, interaction, 1, "USD", "TRY")

    @app_commands.command(name="euro", description="Euro/TL kurunu göster")
    async def euro(self, interaction: discord.Interaction):
        await self.currency.callback(self, interaction, 1, "EUR", "TRY")

    # ==================== ÇEVİRİ ====================

    @app_commands.command(name="translate", description="Metni çevir")
    @app_commands.describe(text="Çevrilecek metin", to_lang="Hedef dil kodu (tr, en, de, fr...)")
    async def translate(self, interaction: discord.Interaction, text: str, to_lang: str = "tr"):
        await interaction.response.defer()
        
        try:
            # LibreTranslate API (ücretsiz, self-hosted olabilir)
            # Alternatif: Google Translate API, DeepL, vb.
            
            # Basit bir ücretsiz API kullan
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text[:500],  # Limit
                "langpair": f"auto|{to_lang}"
            }
            
            async with self.session.get(url, params=params) as resp:
                data = await resp.json()
            
            if data["responseStatus"] != 200:
                return await interaction.followup.send("❌ Çeviri başarısız!")
            
            translated = data["responseData"]["translatedText"]
            detected = data["responseData"].get("detectedLanguage", "auto")
            
            embed = discord.Embed(
                title="🌐 Çeviri",
                color=discord.Color.blue()
            )
            embed.add_field(name="Orijinal", value=text[:1000], inline=False)
            embed.add_field(name=f"Çeviri ({to_lang})", value=translated[:1000], inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Çeviri hatası: {e}")

    # ==================== POLL ====================

    @app_commands.command(name="poll", description="Anket oluştur")
    @app_commands.describe(
        question="Soru",
        option1="Seçenek 1",
        option2="Seçenek 2",
        option3="Seçenek 3 (opsiyonel)",
        option4="Seçenek 4 (opsiyonel)"
    )
    async def poll(
        self, 
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None
    ):
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        
        description = ""
        for i, opt in enumerate(options):
            description += f"{emojis[i]} {opt}\n"
        
        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Anket: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(options)):
            await message.add_reaction(emojis[i])

    # ==================== PING & BOT INFO ====================

    @app_commands.command(name="ping", description="Bot gecikmesini göster")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green() if latency < 200 else discord.Color.orange()
        )
        embed.add_field(name="Gecikme", value=f"{latency}ms", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Bot hakkında bilgi")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📊 Sunucular", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Kullanıcılar", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="🏓 Gecikme", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        embed.add_field(name="⚙️ Versiyon", value="Lithium Bot v2.0", inline=True)
        embed.add_field(name="🐍 Python", value="3.11+", inline=True)
        embed.add_field(name="📚 Discord.py", value=discord.__version__, inline=True)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ExtendedUtility(bot))
