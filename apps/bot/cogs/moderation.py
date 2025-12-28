import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from sqlalchemy import select
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import ModerationCase, CaseNote
from apps.bot.i18n import translate
from apps.bot.utils.permissions import check_command_permission

logger = logging.getLogger("lithium-bot")

class ConfirmationView(discord.ui.View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.Color.red())
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.Color.light_grey())
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_mod_embed(self, title: str, color: discord.Color, user: discord.User, moderator: discord.User, reason: str, case_id: int = None):
        embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
        embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        if case_id:
            embed.set_footer(text=f"Case #{case_id}")
        return embed

    async def reason_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        reasons = ["Spam", "Toxic behavior", "Advertising", "NSFW Content", "Raiding"]
        return [
            app_commands.Choice(name=reason, value=reason)
            for reason in reasons if current.lower() in reason.lower()
        ]

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(moderation_reason="Select a reason or type your own")
    @app_commands.autocomplete(moderation_reason=reason_autocomplete)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, moderation_reason: str = "No reason provided", delete_messages: bool = False):
        if not await check_command_permission(interaction, "ban"):
            return await interaction.response.send_message(translate("perm_denied", lang="en"), ephemeral=True)

        if interaction.user.top_role <= user.top_role:
            return await interaction.response.send_message("❌ You cannot ban someone with a higher or equal role.", ephemeral=True)

        # Confirmation Flow
        view = ConfirmationView()
        await interaction.response.send_message(f"Are you sure you want to ban {user.mention}?", view=view, ephemeral=True)
        await view.wait()

        if view.value is None:
            return await interaction.edit_original_response(content="Timed out.", view=None)
        elif not view.value:
            return await interaction.edit_original_response(content="Cancelled.", view=None)

        # DM Appeal Link (Placeholder)
        try:
            appeal_link = "https://your-bot.com/appeals"
            await user.send(f"You have been banned from {interaction.guild.name}. You can appeal here: {appeal_link}")
        except: pass

        delete_seconds = 604800 if delete_messages else 0
        await user.ban(reason=moderation_reason, delete_message_seconds=delete_seconds)
        
        async with AsyncSessionLocal() as db:
            case = ModerationCase(
                guild_id=str(interaction.guild_id),
                user_id=str(user.id),
                moderator_id=str(interaction.user.id),
                action_type="BAN",
                reason=moderation_reason
            )
            db.add(case)
            await db.commit()
            await db.refresh(case)
            case_id = case.id

        embed = self.create_mod_embed(translate("user_banned", user=user.name), discord.Color.red(), user, interaction.user, moderation_reason, case_id)
        await interaction.edit_original_response(content=None, embed=embed, view=None)

    @app_commands.command(name="softban", description="Ban and immediate unban to clear messages")
    @app_commands.checks.has_permissions(ban_members=True)
    async def softban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Softban"):
        if not await check_command_permission(interaction, "softban"):
            return await interaction.response.send_message(translate("perm_denied", lang="en"), ephemeral=True)

        if interaction.user.top_role <= user.top_role:
            return await interaction.response.send_message("❌ You cannot softban someone with a higher or equal role.", ephemeral=True)

        await user.ban(reason=reason, delete_message_seconds=604800)
        await interaction.guild.unban(user, reason="Softban completion")
        
        async with AsyncSessionLocal() as db:
            case = ModerationCase(
                guild_id=str(interaction.guild_id),
                user_id=str(user.id),
                moderator_id=str(interaction.user.id),
                action_type="SOFTBAN",
                reason=reason
            )
            db.add(case)
            await db.commit()
            await db.refresh(case)
            case_id = case.id

        embed = self.create_mod_embed(translate("user_softbanned", lang="en"), discord.Color.orange(), user, interaction.user, reason, case_id)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, moderation_reason: str = "No reason provided"):
        if not await check_command_permission(interaction, "kick"):
            return await interaction.response.send_message(translate("perm_denied", lang="en"), ephemeral=True)

        if interaction.user.top_role <= user.top_role:
            return await interaction.response.send_message("❌ You cannot kick someone with a higher or equal role.", ephemeral=True)

        await user.kick(reason=moderation_reason)
        
        async with AsyncSessionLocal() as db:
            case = ModerationCase(
                guild_id=str(interaction.guild_id),
                user_id=str(user.id),
                moderator_id=str(interaction.user.id),
                action_type="KICK",
                reason=moderation_reason
            )
            db.add(case)
            await db.commit()
            await db.refresh(case)
            case_id = case.id

        embed = self.create_mod_embed(translate("user_kicked", lang="en", user=user.name), discord.Color.gold(), user, interaction.user, moderation_reason, case_id)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="note", description="Add a note to a moderation case")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def add_note(self, interaction: discord.Interaction, case_id: int, content: str):
        async with AsyncSessionLocal() as db:
            # Check if case exists
            case = await db.get(ModerationCase, case_id)
            if not case or case.guild_id != str(interaction.guild_id):
                return await interaction.response.send_message("❌ Case not found.", ephemeral=True)
            
            note = CaseNote(
                case_id=case_id,
                moderator_id=str(interaction.user.id),
                content=content
            )
            db.add(note)
            await db.commit()
        
        await interaction.response.send_message(f"✅ Added note to Case #{case_id}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
