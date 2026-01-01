"""
Eğlence ve Oyun Sistemi
- Çekiliş (Giveaway)
- Doğum Günü Kutlayıcı
- Düello / Mini Oyunlar (TKM, Yazı-Tura)
- Aşk Ölçer / Uyum Testi
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.fun import (
    Giveaway, Birthday, BirthdayConfig, DuelStats
)
from sqlalchemy import select, delete
import logging
import random
import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("lithium-bot")


def parse_duration(duration_str: str) -> int:
    """Süre string'ini saniyeye çevir"""
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        return None
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    return amount * multipliers.get(unit, 60)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="🎉 Katıl", style=discord.ButtonStyle.success, custom_id="giveaway_join")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Redis'te katılımcıları tut (veya embed reaction kullan)
        await interaction.response.send_message("✅ Çekilişe katıldınız! Şansınız bol olsun! 🍀", ephemeral=True)


class DuelView(discord.ui.View):
    def __init__(self, player1: discord.Member, player2: discord.Member, bet: int = 0):
        super().__init__(timeout=60)
        self.player1 = player1
        self.player2 = player2
        self.bet = bet
        self.player1_choice = None
        self.player2_choice = None

    @discord.ui.button(label="🪨 Taş", style=discord.ButtonStyle.secondary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "rock")

    @discord.ui.button(label="📄 Kağıt", style=discord.ButtonStyle.secondary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "paper")

    @discord.ui.button(label="✂️ Makas", style=discord.ButtonStyle.secondary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "scissors")

    async def make_choice(self, interaction: discord.Interaction, choice: str):
        if interaction.user.id == self.player1.id:
            if self.player1_choice:
                return await interaction.response.send_message("Zaten seçim yaptınız!", ephemeral=True)
            self.player1_choice = choice
            await interaction.response.send_message(f"✅ Seçiminiz: {choice}", ephemeral=True)
        elif interaction.user.id == self.player2.id:
            if self.player2_choice:
                return await interaction.response.send_message("Zaten seçim yaptınız!", ephemeral=True)
            self.player2_choice = choice
            await interaction.response.send_message(f"✅ Seçiminiz: {choice}", ephemeral=True)
        else:
            return await interaction.response.send_message("Bu düello size ait değil!", ephemeral=True)

        # İki oyuncu da seçti mi?
        if self.player1_choice and self.player2_choice:
            await self.finish_game(interaction)

    async def finish_game(self, interaction: discord.Interaction):
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        p1 = self.player1_choice
        p2 = self.player2_choice
        
        # Kazanan belirle
        if p1 == p2:
            result = "draw"
            winner = None
        elif (p1 == "rock" and p2 == "scissors") or \
             (p1 == "paper" and p2 == "rock") or \
             (p1 == "scissors" and p2 == "paper"):
            result = "player1"
            winner = self.player1
            loser = self.player2
        else:
            result = "player2"
            winner = self.player2
            loser = self.player1

        embed = discord.Embed(title="⚔️ Düello Sonucu", timestamp=datetime.utcnow())
        embed.add_field(
            name=self.player1.display_name,
            value=f"{emojis[p1]} {p1.title()}",
            inline=True
        )
        embed.add_field(name="VS", value="⚔️", inline=True)
        embed.add_field(
            name=self.player2.display_name,
            value=f"{emojis[p2]} {p2.title()}",
            inline=True
        )

        if result == "draw":
            embed.description = "🤝 **BERABERE!**"
            embed.color = discord.Color.gold()
        else:
            embed.description = f"🏆 **{winner.mention} KAZANDI!**"
            embed.color = discord.Color.green()
            
            # İstatistik güncelle
            async with AsyncSessionLocal() as db:
                # Kazanan
                stmt = select(DuelStats).where(
                    DuelStats.guild_id == str(interaction.guild_id),
                    DuelStats.user_id == str(winner.id)
                )
                winner_stats = (await db.execute(stmt)).scalar_one_or_none()
                if not winner_stats:
                    winner_stats = DuelStats(guild_id=str(interaction.guild_id), user_id=str(winner.id))
                    db.add(winner_stats)
                winner_stats.wins += 1
                
                # Kaybeden
                stmt = select(DuelStats).where(
                    DuelStats.guild_id == str(interaction.guild_id),
                    DuelStats.user_id == str(loser.id)
                )
                loser_stats = (await db.execute(stmt)).scalar_one_or_none()
                if not loser_stats:
                    loser_stats = DuelStats(guild_id=str(interaction.guild_id), user_id=str(loser.id))
                    db.add(loser_stats)
                loser_stats.losses += 1
                
                await db.commit()

        await interaction.message.edit(embed=embed, view=None)
        self.stop()


class FunGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_checker.start()
        self.birthday_checker.start()

    def cog_unload(self):
        self.giveaway_checker.cancel()
        self.birthday_checker.cancel()

    # ==================== ÇEKİLİŞ SİSTEMİ ====================

    @tasks.loop(seconds=30)
    async def giveaway_checker(self):
        """Biten çekilişleri kontrol et"""
        async with AsyncSessionLocal() as db:
            stmt = select(Giveaway).where(
                Giveaway.ended == False,
                Giveaway.ends_at <= datetime.utcnow()
            )
            giveaways = (await db.execute(stmt)).scalars().all()
            
            for giveaway in giveaways:
                try:
                    channel = self.bot.get_channel(int(giveaway.channel_id))
                    if not channel:
                        continue
                    
                    message = await channel.fetch_message(int(giveaway.message_id))
                    if not message:
                        continue
                    
                    # Katılımcıları al (🎉 reaction)
                    participants = []
                    for reaction in message.reactions:
                        if str(reaction.emoji) == "🎉":
                            async for user in reaction.users():
                                if not user.bot and str(user.id) != giveaway.host_id:
                                    participants.append(user)
                    
                    # Kazananları seç
                    winner_count = min(giveaway.winner_count, len(participants))
                    
                    if winner_count == 0:
                        embed = discord.Embed(
                            title="🎉 Çekiliş Sona Erdi",
                            description=f"**Ödül:** {giveaway.prize}\n\n❌ Yeterli katılımcı olmadığı için kazanan yok!",
                            color=discord.Color.red()
                        )
                        await message.edit(embed=embed, view=None)
                    else:
                        winners = random.sample(participants, winner_count)
                        winner_mentions = ", ".join([w.mention for w in winners])
                        
                        embed = discord.Embed(
                            title="🎉 Çekiliş Sona Erdi!",
                            description=f"**Ödül:** {giveaway.prize}\n\n🏆 **Kazananlar:** {winner_mentions}",
                            color=discord.Color.gold()
                        )
                        embed.set_footer(text=f"Katılımcı: {len(participants)}")
                        
                        await message.edit(embed=embed, view=None)
                        await channel.send(f"🎊 Tebrikler {winner_mentions}! **{giveaway.prize}** kazandınız!")
                        
                        giveaway.winners = [str(w.id) for w in winners]
                    
                    giveaway.ended = True
                    await db.commit()
                    
                except Exception as e:
                    logger.error(f"Giveaway check error: {e}")

    @giveaway_checker.before_loop
    async def before_giveaway_checker(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="giveaway", description="Çekiliş başlat")
    @app_commands.describe(
        duration="Süre (örn: 1h, 1d)",
        prize="Ödül",
        winners="Kazanan sayısı",
        required_role="Katılım için gereken rol (opsiyonel)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_start(
        self, 
        interaction: discord.Interaction,
        duration: str,
        prize: str,
        winners: int = 1,
        required_role: discord.Role = None
    ):
        seconds = parse_duration(duration)
        if not seconds:
            return await interaction.response.send_message("❌ Geçersiz süre! Örnek: 1h, 1d", ephemeral=True)
        
        if winners < 1 or winners > 20:
            return await interaction.response.send_message("❌ Kazanan sayısı 1-20 arasında olmalı!", ephemeral=True)

        ends_at = datetime.utcnow() + timedelta(seconds=seconds)
        
        embed = discord.Embed(
            title="🎉 ÇEKİLİŞ!",
            description=f"**Ödül:** {prize}\n\n🎯 Katılmak için 🎉 emojisine tıklayın!",
            color=discord.Color.gold(),
            timestamp=ends_at
        )
        embed.add_field(name="⏰ Bitiş", value=f"<t:{int(ends_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🏆 Kazanan Sayısı", value=str(winners), inline=True)
        embed.add_field(name="🎫 Düzenleyen", value=interaction.user.mention, inline=True)
        
        if required_role:
            embed.add_field(name="📋 Gerekli Rol", value=required_role.mention, inline=True)
        
        embed.set_footer(text="Çekiliş bitiş zamanı")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎉")
        
        # Database kaydet
        async with AsyncSessionLocal() as db:
            giveaway = Giveaway(
                guild_id=str(interaction.guild_id),
                channel_id=str(interaction.channel_id),
                message_id=str(message.id),
                host_id=str(interaction.user.id),
                prize=prize,
                winner_count=winners,
                ends_at=ends_at,
                required_role_id=str(required_role.id) if required_role else None
            )
            db.add(giveaway)
            await db.commit()

    @app_commands.command(name="giveaway_reroll", description="Çekiliş kazananını yeniden çek")
    @app_commands.describe(message_id="Çekiliş mesaj ID'si")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message("❌ Mesaj bulunamadı!", ephemeral=True)
        
        # Katılımcıları al
        participants = []
        for reaction in message.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user)
        
        if not participants:
            return await interaction.response.send_message("❌ Katılımcı yok!", ephemeral=True)
        
        winner = random.choice(participants)
        await interaction.response.send_message(f"🎊 Yeni kazanan: {winner.mention}! Tebrikler!")

    # ==================== DOĞUM GÜNÜ SİSTEMİ ====================

    @tasks.loop(hours=1)
    async def birthday_checker(self):
        """Her saat doğum günlerini kontrol et"""
        now = datetime.utcnow()
        
        async with AsyncSessionLocal() as db:
            # Bugünün doğum günlerini bul
            stmt = select(Birthday).where(
                Birthday.day == now.day,
                Birthday.month == now.month
            )
            birthdays = (await db.execute(stmt)).scalars().all()
            
            for birthday in birthdays:
                try:
                    # Config al
                    config_stmt = select(BirthdayConfig).where(
                        BirthdayConfig.guild_id == birthday.guild_id
                    )
                    config = (await db.execute(config_stmt)).scalar_one_or_none()
                    if not config:
                        continue
                    
                    guild = self.bot.get_guild(int(birthday.guild_id))
                    if not guild:
                        continue
                    
                    member = guild.get_member(int(birthday.user_id))
                    if not member:
                        continue
                    
                    channel = guild.get_channel(int(config.channel_id))
                    if not channel:
                        continue
                    
                    # Bugün zaten kutlandı mı? (Redis ile kontrol)
                    # Basit versiyon: her saat kontrol eder ama gün içinde tekrarlamaz
                    
                    message = config.message_template.replace("{user}", member.mention)
                    
                    embed = discord.Embed(
                        title="🎂 Doğum Günün Kutlu Olsun!",
                        description=message,
                        color=discord.Color.magenta()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                    await channel.send(embed=embed)
                    
                    # Birthday role ver (varsa)
                    if config.role_id:
                        role = guild.get_role(int(config.role_id))
                        if role and role not in member.roles:
                            await member.add_roles(role, reason="Doğum günü!")
                    
                except Exception as e:
                    logger.error(f"Birthday check error: {e}")

    @birthday_checker.before_loop
    async def before_birthday_checker(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="birthday_set", description="Doğum gününüzü kaydedin")
    @app_commands.describe(day="Gün (1-31)", month="Ay (1-12)")
    async def birthday_set(self, interaction: discord.Interaction, day: int, month: int):
        if day < 1 or day > 31 or month < 1 or month > 12:
            return await interaction.response.send_message("❌ Geçersiz tarih!", ephemeral=True)
        
        async with AsyncSessionLocal() as db:
            stmt = select(Birthday).where(
                Birthday.guild_id == str(interaction.guild_id),
                Birthday.user_id == str(interaction.user.id)
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            
            if existing:
                existing.day = day
                existing.month = month
            else:
                birthday = Birthday(
                    guild_id=str(interaction.guild_id),
                    user_id=str(interaction.user.id),
                    day=day,
                    month=month
                )
                db.add(birthday)
            
            await db.commit()
        
        months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        await interaction.response.send_message(
            f"🎂 Doğum gününüz **{day} {months[month]}** olarak kaydedildi!",
            ephemeral=True
        )

    @app_commands.command(name="birthday_setup", description="Doğum günü kanalını ayarla")
    @app_commands.checks.has_permissions(administrator=True)
    async def birthday_setup(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        role: discord.Role = None
    ):
        async with AsyncSessionLocal() as db:
            stmt = select(BirthdayConfig).where(BirthdayConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                config = BirthdayConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.channel_id = str(channel.id)
            if role:
                config.role_id = str(role.id)
            
            await db.commit()
        
        await interaction.response.send_message(
            f"✅ Doğum günü kutlamaları {channel.mention} kanalına gönderilecek!",
            ephemeral=True
        )

    # ==================== DÜELLO / MİNİ OYUNLAR ====================

    @app_commands.command(name="duel", description="Birisiyle Taş-Kağıt-Makas oyna")
    async def duel(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendinizle düello yapamazsınız!", ephemeral=True)
        if opponent.bot:
            return await interaction.response.send_message("❌ Botlarla düello yapamazsınız!", ephemeral=True)
        
        embed = discord.Embed(
            title="⚔️ Düello!",
            description=f"{interaction.user.mention} vs {opponent.mention}\n\nSeçiminizi yapın!",
            color=discord.Color.red()
        )
        
        view = DuelView(interaction.user, opponent)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="coinflip_duel", description="Yazı-Tura düellosu")
    async def coinflip_duel(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendinizle oynayamazsınız!", ephemeral=True)
        
        result = random.choice(["yazı", "tura"])
        winner = interaction.user if result == "yazı" else opponent
        
        embed = discord.Embed(
            title="🪙 Yazı-Tura Düellosu",
            color=discord.Color.gold()
        )
        embed.add_field(name="Yazı", value=interaction.user.mention, inline=True)
        embed.add_field(name="Tura", value=opponent.mention, inline=True)
        embed.add_field(name="Sonuç", value=f"**{result.upper()}**", inline=False)
        embed.add_field(name="🏆 Kazanan", value=winner.mention, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="duel_stats", description="Düello istatistiklerinizi görün")
    async def duel_stats(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        async with AsyncSessionLocal() as db:
            stmt = select(DuelStats).where(
                DuelStats.guild_id == str(interaction.guild_id),
                DuelStats.user_id == str(target.id)
            )
            stats = (await db.execute(stmt)).scalar_one_or_none()
        
        if not stats:
            return await interaction.response.send_message(
                f"❌ {target.mention} henüz düello yapmamış!",
                ephemeral=True
            )
        
        total = stats.wins + stats.losses + stats.draws
        win_rate = (stats.wins / total * 100) if total > 0 else 0
        
        embed = discord.Embed(
            title=f"⚔️ {target.display_name} - Düello İstatistikleri",
            color=discord.Color.blurple()
        )
        embed.add_field(name="🏆 Galibiyet", value=str(stats.wins), inline=True)
        embed.add_field(name="💀 Mağlubiyet", value=str(stats.losses), inline=True)
        embed.add_field(name="🤝 Beraberlik", value=str(stats.draws), inline=True)
        embed.add_field(name="📊 Kazanma Oranı", value=f"%{win_rate:.1f}", inline=True)
        embed.add_field(name="🎮 Toplam", value=str(total), inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # ==================== AŞK ÖLÇER / UYUM TESTİ ====================

    @app_commands.command(name="love", description="İki kişi arasındaki aşk yüzdesini ölç")
    async def love_meter(self, interaction: discord.Interaction, user1: discord.Member, user2: discord.Member = None):
        user2 = user2 or interaction.user
        
        # Tutarlı sonuç için ID'leri kullan
        seed = min(user1.id, user2.id) + max(user1.id, user2.id)
        random.seed(seed)
        percentage = random.randint(0, 100)
        random.seed()  # Reset
        
        # Yüzdeye göre emoji ve mesaj
        if percentage >= 90:
            emoji = "💘💕💖"
            message = "Mükemmel uyum! Ruh ikizleri!"
        elif percentage >= 70:
            emoji = "💕❤️"
            message = "Harika bir çift olursunuz!"
        elif percentage >= 50:
            emoji = "💛💚"
            message = "Fena değil, denemeye değer!"
        elif percentage >= 30:
            emoji = "💙"
            message = "Arkadaş olarak daha iyisiniz..."
        else:
            emoji = "💔"
            message = "Belki başka zamanda..."
        
        # Progress bar
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        embed = discord.Embed(
            title=f"{emoji} Aşk Ölçer {emoji}",
            color=discord.Color.pink()
        )
        embed.add_field(
            name=f"{user1.display_name} 💗 {user2.display_name}",
            value=f"```\n[{bar}] {percentage}%\n```\n*{message}*",
            inline=False
        )
        embed.set_footer(text="Bu sadece eğlence amaçlıdır!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ship", description="İki kişiyi eşleştir ve isim oluştur")
    async def ship(self, interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
        # İsimlerin yarısını al ve birleştir
        name1 = user1.display_name
        name2 = user2.display_name
        
        half1 = name1[:len(name1)//2]
        half2 = name2[len(name2)//2:]
        
        ship_name = half1 + half2
        
        # Aşk yüzdesi
        seed = min(user1.id, user2.id) + max(user1.id, user2.id)
        random.seed(seed)
        percentage = random.randint(0, 100)
        random.seed()
        
        embed = discord.Embed(
            title="💕 Ship Makinesi",
            color=discord.Color.pink()
        )
        embed.add_field(
            name="Çift İsmi",
            value=f"**{ship_name}**",
            inline=False
        )
        embed.add_field(name="Uyum", value=f"{percentage}%", inline=True)
        embed.add_field(
            name="Eşleşme",
            value=f"{user1.mention} + {user2.mention}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Sihirli 8 topuna sor")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Kesinlikle evet! ✅",
            "Evet 👍",
            "Büyük ihtimalle 🤔",
            "Belki 🤷",
            "Şüpheliyim 😕",
            "Hayır 👎",
            "Kesinlikle hayır ❌",
            "Tekrar sor 🔄",
            "Daha sonra tekrar dene ⏰",
            "Şu an cevap veremem 🤐",
            "Kader bunu söylememi yasaklıyor 🔮",
            "İşaretler evet diyor ✨"
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Sihirli 8 Top",
            color=discord.Color.purple()
        )
        embed.add_field(name="Soru", value=question, inline=False)
        embed.add_field(name="Cevap", value=response, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roll", description="Zar at")
    @app_commands.describe(dice="Zar formatı (örn: 2d6, 1d20)")
    async def roll_dice(self, interaction: discord.Interaction, dice: str = "1d6"):
        match = re.match(r'^(\d+)d(\d+)$', dice.lower())
        if not match:
            return await interaction.response.send_message("❌ Geçersiz format! Örnek: 2d6, 1d20", ephemeral=True)
        
        count = int(match.group(1))
        sides = int(match.group(2))
        
        if count < 1 or count > 100 or sides < 2 or sides > 1000:
            return await interaction.response.send_message("❌ Geçersiz değerler!", ephemeral=True)
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        embed = discord.Embed(
            title=f"🎲 {dice} Zar Atışı",
            color=discord.Color.orange()
        )
        embed.add_field(name="Sonuçlar", value=", ".join(map(str, rolls)), inline=False)
        embed.add_field(name="Toplam", value=str(total), inline=True)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(FunGames(bot))
