import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.tickets import Ticket, TicketConfig
from lithium_core.models.core import Guild
import asyncio
from sqlalchemy import select
import logging

class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Check if enabled
        async with AsyncSessionLocal() as db:
            stmt = select(Guild).where(Guild.id == str(interaction.guild_id))
            guild_config = (await db.execute(stmt)).scalar_one_or_none()
            if not guild_config or not guild_config.tickets_enabled:
                return await interaction.followup.send("Tickets are currently disabled!", ephemeral=True)

            # Check if already has an open ticket
        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(Ticket).where(Ticket.user_id == str(interaction.user.id), Ticket.status == "open"))
            if existing.scalar_one_or_none():
                return await interaction.followup.send("You already have an open ticket!", ephemeral=True)
            
            # Create channel
            channel = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}")
            await channel.set_permissions(interaction.guild.default_role, read_messages=False)
            await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
            
            # Save to DB
            ticket = Ticket(guild_id=str(interaction.guild.id), channel_id=str(channel.id), user_id=str(interaction.user.id))
            db.add(ticket)
            await db.commit()
            
            await channel.send(f"Welcome {interaction.user.mention}! Support will be with you shortly. Use `/close` to finish.")
            await interaction.followup.send(f"Ticket opened in {channel.mention}", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_tickets", description="Setup ticket opening message")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction, channel: discord.TextChannel):
        view = TicketView(self.bot)
        embed = discord.Embed(title="Support Tickets", description="Click the button below to open a ticket.", color=discord.Color.blue())
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("Ticket setup complete.", ephemeral=True)

    @app_commands.command(name="close", description="Close current ticket")
    async def close(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Ticket).where(Ticket.channel_id == str(interaction.channel.id)))
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
                
            ticket.status = "closed"
            await db.commit()
            
            await interaction.response.send_message("Ticket closed. This channel will be deleted in 10 seconds.")
            await asyncio.sleep(10)
            await interaction.channel.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))
