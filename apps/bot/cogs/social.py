import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.social import ReactionRoleMenu, ReactionRoleItem
from sqlalchemy import select

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reaction_role", description="Create a reaction role menu")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_menu(self, interaction: discord.Interaction, title: str, description: str):
        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        await interaction.response.send_message("Creating menu...", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        
        async with AsyncSessionLocal() as db:
            menu = ReactionRoleMenu(
                guild_id=str(interaction.guild_id),
                message_id=str(message.id),
                channel_id=str(interaction.channel_id),
                title=title,
                description=description
            )
            db.add(menu)
            await db.commit()
            await interaction.followup.send(f"Menu created! Use `/add_reaction_role` with ID {menu.id}", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return
            
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ReactionRoleItem).join(ReactionRoleMenu).where(
                ReactionRoleMenu.message_id == str(payload.message_id),
                ReactionRoleItem.emoji == str(payload.emoji)
            ))
            item = result.scalar_one_or_none()
            
            if item:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(int(item.role_id))
                if role:
                    await payload.member.add_roles(role)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
