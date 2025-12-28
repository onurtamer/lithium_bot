import discord
from discord.ext import commands
import logging
from sqlalchemy import select
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import LogRoute

logger = logging.getLogger("lithium-bot")

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild_id: int, module: str) -> discord.TextChannel:
        async with AsyncSessionLocal() as db:
            stmt = select(LogRoute).where(
                LogRoute.guild_id == str(guild_id),
                LogRoute.module == module.upper()
            )
            route = (await db.execute(stmt)).scalar_one_or_none()
            if not route:
                return None
            
            return self.bot.get_channel(int(route.channel_id))

    async def send_log(self, guild_id: int, module: str, embed: discord.Embed):
        channel = await self.get_log_channel(guild_id, module)
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send log to {channel.id}: {e}")

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You lack permissions for this.", ephemeral=True)
        else:
            logger.error(f"Command Error: {error}")
            embed = discord.Embed(title="Command Error", description=f"```py\n{error}\n```", color=discord.Color.red())
            embed.add_field(name="Command", value=interaction.command.name if interaction.command else "Unknown")
            embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})")
            
            # Route to a generic 'SYSTEM' or 'MODERATION' log for errors
            await self.send_log(interaction.guild_id, "MODERATION", embed)
            
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An internal error occurred.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Logging(bot))
