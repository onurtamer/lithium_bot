import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.tickets import Ticket, TicketConfig
from lithium_core.models.core import Guild
import asyncio
from sqlalchemy import select
import logging
import io

class TicketControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions logic could be enhanced here to check DB support role
        # For now, stick to permission check or admin
        if not interaction.user.guild_permissions.manage_messages:
             return await interaction.response.send_message("❌ You are not authroized.", ephemeral=True)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Ticket).where(Ticket.channel_id == str(interaction.channel.id)))
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
            
            if ticket.claimed_by:
                return await interaction.response.send_message(f"Ticket already claimed by <@{ticket.claimed_by}>", ephemeral=True) 
            
            ticket.claimed_by = str(interaction.user.id)
            ticket.status = "CLAIMED"
            await db.commit()
            
        await interaction.response.send_message(f"✅ Ticket claimed by {interaction.user.mention}!")

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket and generating transcript...", ephemeral=True)
        
        # Generate Transcript
        messages = [message async for message in interaction.channel.history(limit=500, oldest_first=True)]
        transcript_text = f"Ticket Transcript - {interaction.channel.name}\nGenerated: {discord.utils.utcnow()}\n\n"
        
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript_text += f"[{timestamp}] {msg.author.name}: {msg.content}\n"
            
        file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"transcript-{interaction.channel.name}.txt")
        
        try:
            await interaction.user.send("Here is the transcript for the closed ticket.", file=file)
        except: pass

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Ticket).where(Ticket.channel_id == str(interaction.channel.id)))
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.status = "CLOSED"
                await db.commit()

        await interaction.channel.send("Ticket closed. Deleting in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketCreateSelect(discord.ui.Select):
    def __init__(self, bot, categories):
        options = []
        for cat in categories:
            # cat is a dict like {"label": "Gen", "value": "gen", "emoji": "❓"}
            options.append(discord.SelectOption(
                label=cat.get("label"), 
                value=cat.get("value"), 
                emoji=cat.get("emoji") if cat.get("emoji") else None,
                description=cat.get("description")
            ))
            
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, custom_id="ticket_category_select", options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        category_name = self.values[0]
        
        async with AsyncSessionLocal() as db:
            # Check existing
            stmt = select(Ticket).where(Ticket.user_id == str(interaction.user.id), Ticket.status != "CLOSED")
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                 return await interaction.followup.send(f"You already have an open ticket: <#{existing.channel_id}>", ephemeral=True)

            # Check config for role
            stmt_conf = select(TicketConfig).where(TicketConfig.guild_id == str(interaction.guild_id))
            config = (await db.execute(stmt_conf)).scalar_one_or_none()
            
            support_role = None
            if config and config.support_role_id:
                support_role = interaction.guild.get_role(int(config.support_role_id))

            # Create Channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            name = f"{category_name}-{interaction.user.name}"
            channel = await interaction.guild.create_text_channel(name, overwrites=overwrites)
            
            ticket = Ticket(
                guild_id=str(interaction.guild.id), 
                channel_id=str(channel.id), 
                user_id=str(interaction.user.id),
                category=category_name,
                status="OPEN"
            )
            db.add(ticket)
            await db.commit()
            
            embed = discord.Embed(title=f"Ticket: {category_name.title()}", description=f"Welcome {interaction.user.mention}!\nSupport will be with you shortly.", color=discord.Color.green())
            view = TicketControlView(self.bot)
            await channel.send(embed=embed, view=view)
            
            await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self, bot, categories):
        super().__init__(timeout=None)
        if not categories:
             # Default fallback
             categories = [{"label": "General Support", "value": "general", "emoji": "❓", "description": "General Help"}]
        self.add_item(TicketCreateSelect(bot, categories))

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_config(self, db, guild_id):
        stmt = select(TicketConfig).where(TicketConfig.guild_id == str(guild_id))
        return (await db.execute(stmt)).scalar_one_or_none()

    @app_commands.command(name="setup_tickets", description="Setup ticket panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        
        async with AsyncSessionLocal() as db:
            config = await self.get_config(db, interaction.guild_id)
            categories = config.categories if config else []
            
        embed = discord.Embed(
            title="🎫 Support Center", 
            description="Select a category below to open a ticket.", 
            color=discord.Color.blurple()
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        
        view = TicketView(self.bot, categories)
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Ticket panel sent to {target_channel.mention}", ephemeral=True)

    @app_commands.command(name="ticket_set_role", description="Set support staff role")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_role(self, interaction: discord.Interaction, role: discord.Role):
        async with AsyncSessionLocal() as db:
            config = await self.get_config(db, interaction.guild_id)
            if not config:
                config = TicketConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            config.support_role_id = str(role.id)
            await db.commit()
            
        await interaction.response.send_message(f"✅ Tickets will now be visible to {role.mention}", ephemeral=True)

    @app_commands.command(name="ticket_add_category", description="Add a new ticket category")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_category(self, interaction: discord.Interaction, label: str, value: str, emoji: str, description: str = None):
        async with AsyncSessionLocal() as db:
            config = await self.get_config(db, interaction.guild_id)
            if not config:
                config = TicketConfig(guild_id=str(interaction.guild_id))
                db.add(config)
            
            # Categories is a list of dicts. JSON mutation in SQLAlchemy needs reassignment 
            # or explicit flag tracking often, but reassigning the list usually works.
            current_cats = list(config.categories) if config.categories else []
            current_cats.append({
                "label": label,
                "value": value.lower(),
                "emoji": emoji,
                "description": description
            })
            config.categories = current_cats
            
            # Force dirty flag if needed (in async session sometimes explicit)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(config, "categories")
            
            await db.commit()
            
        await interaction.response.send_message(f"✅ Added category: **{label}**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
