"""
Gelişmiş Tepki Rolleri (Reaction Roles) Sistemi
- Reaction role mesajı oluşturma
- Emoji-rol eşleştirme
- Çoklu rol desteği
"""
import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import ReactionRoleMenu
from sqlalchemy import select
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("lithium-bot")


class ReactionRoleSetupView(discord.ui.View):
    def __init__(self, author_id: int, roles_mapping: dict):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.roles_mapping = roles_mapping  # {emoji: role_id}
        self.message_id = None

    @discord.ui.button(label="✅ Onayla ve Gönder", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Bu sizin değil!", ephemeral=True)
        
        self.stop()
        await interaction.response.send_message("✅ Reaction role mesajı gönderildi!", ephemeral=True)

    @discord.ui.button(label="❌ İptal", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Bu sizin değil!", ephemeral=True)
        
        self.roles_mapping = None
        self.stop()
        await interaction.response.send_message("❌ İptal edildi.", ephemeral=True)


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Reaction eklendiğinde rol ver"""
        if payload.member.bot:
            return
        
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(
                ReactionRoleMenu.message_id == str(payload.message_id)
            )
            menu = (await db.execute(stmt)).scalar_one_or_none()
            if not menu:
                return
            
            emoji_str = str(payload.emoji)
            if emoji_str not in menu.options:
                return
            
            role_id = int(menu.options[emoji_str])
            role = payload.member.guild.get_role(role_id)
            
            if role and role not in payload.member.roles:
                try:
                    await payload.member.add_roles(role, reason="Reaction Role")
                except discord.Forbidden:
                    logger.error(f"Cannot add role {role.name} to {payload.member}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Reaction kaldırıldığında rolü al"""
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(
                ReactionRoleMenu.message_id == str(payload.message_id)
            )
            menu = (await db.execute(stmt)).scalar_one_or_none()
            if not menu:
                return
            
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if not member or member.bot:
                return
            
            emoji_str = str(payload.emoji)
            if emoji_str not in menu.options:
                return
            
            role_id = int(menu.options[emoji_str])
            role = guild.get_role(role_id)
            
            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason="Reaction Role")
                except discord.Forbidden:
                    logger.error(f"Cannot remove role {role.name} from {member}")

    @app_commands.command(name="reactionrole", description="Reaction role mesajı oluştur")
    @app_commands.describe(
        channel="Mesajın gönderileceği kanal",
        title="Mesaj başlığı",
        description="Mesaj açıklaması"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_setup(
        self, 
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str = "🎭 Rol Seçimi",
        description: str = "Aşağıdaki emojilere tıklayarak rol alabilirsiniz!"
    ):
        await interaction.response.send_message(
            "📝 Şimdi rol eşleştirmelerini girin. Her satırda bir emoji ve rol yazın:\n"
            "Örnek: `🎮 Oyuncu, 🎵 Müzik Sever, 🎨 Sanatçı`\n\n"
            "Formatı takip edin: `emoji1 @rol1, emoji2 @rol2, ...`\n\n"
            "**Yanıtınızı 60 saniye içinde gönderin:**",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
        except:
            return await interaction.followup.send("❌ Zaman aşımı!", ephemeral=True)
        
        # Parse input
        roles_mapping = {}
        content = msg.content
        
        # Basit: virgülle ayrılmış "emoji @rol" çiftleri
        pairs = content.split(",")
        
        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue
            
            # Emoji ve rol mention'ı ayır
            parts = pair.split()
            if len(parts) < 2:
                continue
            
            emoji = parts[0]
            
            # Rol mention'ı bul
            role = None
            for part in parts[1:]:
                if part.startswith("<@&") and part.endswith(">"):
                    role_id = int(part[3:-1])
                    role = interaction.guild.get_role(role_id)
                    break
            
            if role:
                roles_mapping[emoji] = str(role.id)
        
        if not roles_mapping:
            return await interaction.followup.send(
                "❌ Geçerli rol eşleştirmesi bulunamadı!\n"
                "Örnek format: `🎮 @Oyuncu, 🎵 @Müzik`",
                ephemeral=True
            )
        
        # Mesajı temizle
        try:
            await msg.delete()
        except:
            pass
        
        # Embed oluştur
        embed = discord.Embed(
            title=title,
            description=description + "\n\n",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        for emoji, role_id in roles_mapping.items():
            role = interaction.guild.get_role(int(role_id))
            if role:
                embed.description += f"{emoji} → {role.mention}\n"
        
        embed.set_footer(text="Emoji'ye tıklayarak rol alabilirsiniz!")
        
        # Mesajı gönder
        reaction_msg = await channel.send(embed=embed)
        
        # Emojileri ekle
        for emoji in roles_mapping.keys():
            try:
                await reaction_msg.add_reaction(emoji)
            except:
                pass
        
        # Database'e kaydet
        async with AsyncSessionLocal() as db:
            menu = ReactionRoleMenu(
                guild_id=str(interaction.guild_id),
                channel_id=str(channel.id),
                message_id=str(reaction_msg.id),
                options=roles_mapping
            )
            db.add(menu)
            await db.commit()
        
        await interaction.followup.send(
            f"✅ Reaction role mesajı {channel.mention} kanalına gönderildi!",
            ephemeral=True
        )

    @app_commands.command(name="reactionrole_add", description="Mevcut reaction role mesajına emoji ekle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_add(
        self, 
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(
                ReactionRoleMenu.message_id == message_id,
                ReactionRoleMenu.guild_id == str(interaction.guild_id)
            )
            menu = (await db.execute(stmt)).scalar_one_or_none()
            
            if not menu:
                return await interaction.response.send_message("❌ Reaction role mesajı bulunamadı!", ephemeral=True)
            
            # Options güncelle
            options = dict(menu.options) if menu.options else {}
            options[emoji] = str(role.id)
            menu.options = options
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(menu, "options")
            
            await db.commit()
        
        # Mesaja emoji ekle
        try:
            channel = interaction.guild.get_channel(int(menu.channel_id))
            if channel:
                msg = await channel.fetch_message(int(message_id))
                await msg.add_reaction(emoji)
        except:
            pass
        
        await interaction.response.send_message(f"✅ {emoji} → {role.mention} eklendi!", ephemeral=True)

    @app_commands.command(name="reactionrole_remove", description="Reaction role mesajından emoji kaldır")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_remove(
        self, 
        interaction: discord.Interaction,
        message_id: str,
        emoji: str
    ):
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(
                ReactionRoleMenu.message_id == message_id,
                ReactionRoleMenu.guild_id == str(interaction.guild_id)
            )
            menu = (await db.execute(stmt)).scalar_one_or_none()
            
            if not menu:
                return await interaction.response.send_message("❌ Reaction role mesajı bulunamadı!", ephemeral=True)
            
            if emoji not in menu.options:
                return await interaction.response.send_message("❌ Bu emoji bulunamadı!", ephemeral=True)
            
            options = dict(menu.options)
            del options[emoji]
            menu.options = options
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(menu, "options")
            
            await db.commit()
        
        await interaction.response.send_message(f"✅ {emoji} kaldırıldı!", ephemeral=True)

    @app_commands.command(name="reactionrole_list", description="Reaction role mesajlarını listele")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_list(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            stmt = select(ReactionRoleMenu).where(
                ReactionRoleMenu.guild_id == str(interaction.guild_id)
            )
            menus = (await db.execute(stmt)).scalars().all()
        
        if not menus:
            return await interaction.response.send_message("❌ Hiç reaction role mesajı yok!", ephemeral=True)
        
        embed = discord.Embed(
            title="🎭 Reaction Role Mesajları",
            color=discord.Color.blurple()
        )
        
        for menu in menus[:10]:
            channel = interaction.guild.get_channel(int(menu.channel_id))
            channel_mention = channel.mention if channel else f"#{menu.channel_id}"
            
            roles_count = len(menu.options) if menu.options else 0
            embed.add_field(
                name=f"Mesaj ID: {menu.message_id}",
                value=f"Kanal: {channel_mention}\nRol sayısı: {roles_count}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
