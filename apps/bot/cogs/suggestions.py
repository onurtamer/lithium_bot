"""
Öneri (Suggestion) Sistemi
- Öneri gönderme
- Oylama
- Moderatör onay/ret
"""
import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.fun import Suggestion, SuggestionConfig
from sqlalchemy import select
import logging
from datetime import datetime

logger = logging.getLogger("lithium-bot")


class SuggestionView(discord.ui.View):
    def __init__(self, suggestion_id: int):
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id

    @discord.ui.button(label="✅ Onayla", style=discord.ButtonStyle.success, custom_id="suggestion_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)
        
        await self.update_status(interaction, "APPROVED", discord.Color.green(), "✅ Onaylandı")

    @discord.ui.button(label="❌ Reddet", style=discord.ButtonStyle.danger, custom_id="suggestion_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)
        
        await self.update_status(interaction, "DENIED", discord.Color.red(), "❌ Reddedildi")

    @discord.ui.button(label="🔧 Uygulandı", style=discord.ButtonStyle.primary, custom_id="suggestion_implement")
    async def implement(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)
        
        await self.update_status(interaction, "IMPLEMENTED", discord.Color.blue(), "🔧 Uygulandı")

    async def update_status(self, interaction: discord.Interaction, status: str, color: discord.Color, label: str):
        async with AsyncSessionLocal() as db:
            stmt = select(Suggestion).where(Suggestion.id == self.suggestion_id)
            suggestion = (await db.execute(stmt)).scalar_one_or_none()
            if suggestion:
                suggestion.status = status
                await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = color
        
        # Status field güncelle veya ekle
        for i, field in enumerate(embed.fields):
            if field.name == "Durum":
                embed.set_field_at(i, name="Durum", value=f"{label} - {interaction.user.mention}", inline=True)
                break
        else:
            embed.add_field(name="Durum", value=f"{label} - {interaction.user.mention}", inline=True)
        
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"✅ Öneri durumu güncellendi: {label}", ephemeral=True)


class SuggestionSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_config(self, guild_id: int) -> SuggestionConfig:
        async with AsyncSessionLocal() as db:
            stmt = select(SuggestionConfig).where(SuggestionConfig.guild_id == str(guild_id))
            return (await db.execute(stmt)).scalar_one_or_none()

    @app_commands.command(name="suggest", description="Bir öneri gönder")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        config = await self.get_config(interaction.guild_id)
        
        if not config:
            return await interaction.response.send_message(
                "❌ Öneri sistemi kurulmamış! Admin `/suggest_setup` kullanmalı.",
                ephemeral=True
            )
        
        channel = interaction.guild.get_channel(int(config.channel_id))
        if not channel:
            return await interaction.response.send_message("❌ Öneri kanalı bulunamadı!", ephemeral=True)

        embed = discord.Embed(
            title="💡 Yeni Öneri",
            description=suggestion,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Durum", value="⏳ Beklemede", inline=True)
        embed.add_field(name="Oylar", value="👍 0 | 👎 0", inline=True)
        
        # Öneriyi gönder
        await interaction.response.defer(ephemeral=True)
        
        view = None  # Manager view'ı daha sonra ekleyeceğiz
        msg = await channel.send(embed=embed)
        
        # Oylama emojileri ekle
        await msg.add_reaction(config.upvote_emoji)
        await msg.add_reaction(config.downvote_emoji)
        
        # Database kaydet
        async with AsyncSessionLocal() as db:
            suggestion_obj = Suggestion(
                guild_id=str(interaction.guild_id),
                channel_id=str(channel.id),
                message_id=str(msg.id),
                author_id=str(interaction.user.id),
                content=suggestion
            )
            db.add(suggestion_obj)
            await db.commit()
            await db.refresh(suggestion_obj)
            
            # View'ı ekle
            view = SuggestionView(suggestion_obj.id)
            await msg.edit(view=view)

        await interaction.followup.send("✅ Öneriniz gönderildi!", ephemeral=True)

    @app_commands.command(name="suggest_setup", description="Öneri kanalını ayarla")
    @app_commands.checks.has_permissions(administrator=True)
    async def suggest_setup(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        upvote_emoji: str = "👍",
        downvote_emoji: str = "👎"
    ):
        async with AsyncSessionLocal() as db:
            stmt = select(SuggestionConfig).where(SuggestionConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()
            
            if not config:
                config = SuggestionConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.channel_id = str(channel.id)
            config.upvote_emoji = upvote_emoji
            config.downvote_emoji = downvote_emoji
            
            await db.commit()

        await interaction.response.send_message(
            f"✅ Öneri kanalı {channel.mention} olarak ayarlandı!\n"
            f"Emojiler: {upvote_emoji} / {downvote_emoji}",
            ephemeral=True
        )

    @app_commands.command(name="suggest_respond", description="Bir öneriye yanıt ver")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def suggest_respond(
        self, 
        interaction: discord.Interaction, 
        message_id: str,
        response: str
    ):
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Suggestion).where(Suggestion.message_id == message_id)
                suggestion = (await db.execute(stmt)).scalar_one_or_none()
                
                if not suggestion:
                    return await interaction.response.send_message("❌ Öneri bulunamadı!", ephemeral=True)
                
                suggestion.staff_response = response
                await db.commit()
                
                # Mesajı güncelle
                channel = interaction.guild.get_channel(int(suggestion.channel_id))
                if channel:
                    msg = await channel.fetch_message(int(suggestion.message_id))
                    embed = msg.embeds[0]
                    
                    # Response field ekle
                    embed.add_field(
                        name="📝 Yetkili Yanıtı",
                        value=f"{response}\n\n*- {interaction.user.mention}*",
                        inline=False
                    )
                    
                    await msg.edit(embed=embed)

            await interaction.response.send_message("✅ Yanıtınız eklendi!", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(SuggestionSystem(bot))
