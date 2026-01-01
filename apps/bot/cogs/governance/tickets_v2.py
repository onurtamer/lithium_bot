"""
Tickets V2 - Enhanced bot-centric ticket system
Report, Complaint, Request, Appeal
"""
import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.governance import (
    TicketV2, TicketMessageV2, TicketType, TicketStatus, ModCase
)
from lithium_core.services.governance_service import GovernanceService
from lithium_core.services.case_service import CaseService
from sqlalchemy import select, func
from datetime import datetime
import logging

logger = logging.getLogger("lithium-bot")


class TicketActionView(discord.ui.View):
    """Ticket action buttons for moderators"""
    
    def __init__(self, ticket_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="Triage Et", style=discord.ButtonStyle.primary, custom_id="ticket_triage")
    async def triage(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as db:
            stmt = select(TicketV2).where(TicketV2.id == self.ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("❌ Ticket bulunamadı!", ephemeral=True)
            
            if ticket.status != TicketStatus.OPENED.value:
                return await interaction.response.send_message("❌ Bu ticket zaten triage edilmiş!", ephemeral=True)
            
            ticket.status = TicketStatus.TRIAGED.value
            ticket.triaged_at = datetime.utcnow()
            ticket.assigned_to = str(interaction.user.id)
            await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.blue()
        embed.add_field(name="Triage", value=f"{interaction.user.mention}", inline=True)
        
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"✅ Ticket size atandı!", ephemeral=True)
    
    @discord.ui.button(label="Review'a Gönder", style=discord.ButtonStyle.secondary, custom_id="ticket_review")
    async def to_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as db:
            stmt = select(TicketV2).where(TicketV2.id == self.ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("❌ Ticket bulunamadı!", ephemeral=True)
            
            ticket.status = TicketStatus.IN_REVIEW.value
            await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.gold()
        embed.set_field_at(-1, name="Durum", value="🔍 In Review")
        
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"✅ Ticket review queue'ya gönderildi!", ephemeral=True)
    
    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="ticket_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as db:
            stmt = select(TicketV2).where(TicketV2.id == self.ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("❌ Ticket bulunamadı!", ephemeral=True)
            
            ticket.status = TicketStatus.CLOSED.value
            ticket.resolution = "denied"
            ticket.closed_at = datetime.utcnow()
            await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        for child in self.children:
            child.disabled = True
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"❌ Ticket reddedildi.", ephemeral=True)
    
    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, custom_id="ticket_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as db:
            stmt = select(TicketV2).where(TicketV2.id == self.ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("❌ Ticket bulunamadı!", ephemeral=True)
            
            ticket.status = TicketStatus.DECIDED.value
            ticket.decided_at = datetime.utcnow()
            ticket.resolution = "approved"
            await db.commit()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        for child in self.children:
            child.disabled = True
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Ticket onaylandı!", ephemeral=True)


class TicketsV2(commands.Cog):
    """Enhanced Ticket System for Bot-Autocracy"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def _generate_ticket_id(self, db, guild_id: str, ticket_type: str) -> str:
        """Generate unique ticket ID"""
        prefix = ticket_type[0].upper()  # R, C, Q, A
        stmt = select(func.count(TicketV2.id)).where(TicketV2.guild_id == guild_id)
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return f"{guild_id[-4:]}-{prefix}-{count + 1:04d}"
    
    async def _create_ticket(
        self,
        interaction: discord.Interaction,
        ticket_type: str,
        title: str,
        description: str,
        subject_id: str = None,
        related_case_id: int = None,
        priority: int = 5
    ) -> TicketV2:
        """Create a new ticket"""
        async with AsyncSessionLocal() as db:
            ticket_id = await self._generate_ticket_id(db, str(interaction.guild_id), ticket_type)
            
            ticket = TicketV2(
                ticket_id=ticket_id,
                guild_id=str(interaction.guild_id),
                ticket_type=ticket_type,
                creator_id=str(interaction.user.id),
                subject_id=subject_id,
                related_case_id=related_case_id,
                priority=priority,
                title=title,
                description=description
            )
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
            
            return ticket
    
    async def _send_to_queue(self, interaction: discord.Interaction, ticket: TicketV2):
        """Send ticket to mod queue channel"""
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            config = await governance_svc.get_or_create_config(str(interaction.guild_id))
        
        # Find appropriate channel (use mod_log for now)
        if config.mod_log_channel_id:
            channel = self.bot.get_channel(int(config.mod_log_channel_id))
            if channel:
                type_emoji = {
                    "report": "🚨",
                    "complaint": "📢",
                    "request": "💡",
                    "appeal": "⚖️"
                }
                
                embed = discord.Embed(
                    title=f"{type_emoji.get(ticket.ticket_type, '📋')} Ticket #{ticket.ticket_id}",
                    description=ticket.description[:1000] if ticket.description else "Açıklama yok",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Tür", value=ticket.ticket_type.upper(), inline=True)
                embed.add_field(name="Öncelik", value=f"{'⭐' * min(10, ticket.priority)}", inline=True)
                embed.add_field(name="Oluşturan", value=f"<@{ticket.creator_id}>", inline=True)
                
                if ticket.subject_id:
                    embed.add_field(name="Konu", value=f"<@{ticket.subject_id}>", inline=True)
                
                embed.add_field(name="Durum", value="📥 Açık", inline=True)
                embed.set_footer(text=f"Ticket ID: {ticket.ticket_id}")
                
                view = TicketActionView(ticket.id)
                await channel.send(embed=embed, view=view)
    
    # ==================== USER COMMANDS ====================
    
    @app_commands.command(name="report", description="Bir kullanıcıyı rapor et")
    @app_commands.describe(
        user="Rapor edilecek kullanıcı",
        reason="Rapor sebebi",
        evidence="Kanıt ekran görüntüsü (opsiyonel)"
    )
    async def report_user(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str,
        evidence: discord.Attachment = None
    ):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendinizi raporlayamazsınız!", ephemeral=True)
        
        if user.bot:
            return await interaction.response.send_message("❌ Botları raporlayamazsınız!", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        description = f"**Sebep:** {reason}"
        if evidence:
            description += f"\n**Kanıt:** {evidence.url}"
        
        ticket = await self._create_ticket(
            interaction,
            ticket_type=TicketType.REPORT.value,
            title=f"Rapor: {user.display_name}",
            description=description,
            subject_id=str(user.id),
            priority=6
        )
        
        await self._send_to_queue(interaction, ticket)
        
        await interaction.followup.send(
            f"✅ Raporunuz alındı!\n"
            f"**Ticket ID:** `{ticket.ticket_id}`\n"
            f"Moderatörler tarafından incelenecektir.",
            ephemeral=True
        )
    
    @app_commands.command(name="complaint", description="Bir şikayet bildir")
    @app_commands.describe(
        subject="Şikayet konusu",
        description="Detaylı açıklama"
    )
    async def complaint(
        self,
        interaction: discord.Interaction,
        subject: str,
        description: str
    ):
        await interaction.response.defer(ephemeral=True)
        
        ticket = await self._create_ticket(
            interaction,
            ticket_type=TicketType.COMPLAINT.value,
            title=subject,
            description=description,
            priority=5
        )
        
        await self._send_to_queue(interaction, ticket)
        
        await interaction.followup.send(
            f"✅ Şikayetiniz alındı!\n"
            f"**Ticket ID:** `{ticket.ticket_id}`",
            ephemeral=True
        )
    
    @app_commands.command(name="request", description="Bir özellik veya etkinlik isteği gönder")
    @app_commands.describe(
        type="İstek türü",
        description="Detaylı açıklama"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Özellik İsteği", value="feature"),
        app_commands.Choice(name="Etkinlik İsteği", value="event"),
        app_commands.Choice(name="Diğer", value="other")
    ])
    async def request_cmd(
        self,
        interaction: discord.Interaction,
        type: str,
        description: str
    ):
        await interaction.response.defer(ephemeral=True)
        
        ticket = await self._create_ticket(
            interaction,
            ticket_type=TicketType.REQUEST.value,
            title=f"{type.title()} İsteği",
            description=description,
            priority=3
        )
        
        await self._send_to_queue(interaction, ticket)
        
        await interaction.followup.send(
            f"✅ İsteğiniz alındı!\n"
            f"**Ticket ID:** `{ticket.ticket_id}`",
            ephemeral=True
        )
    
    @app_commands.command(name="appeal", description="Bir cezaya itiraz et")
    @app_commands.describe(
        case_id="Case ID (opsiyonel - biliniyorsa)",
        reason="İtiraz sebebiniz"
    )
    async def appeal(
        self,
        interaction: discord.Interaction,
        reason: str,
        case_id: str = None
    ):
        await interaction.response.defer(ephemeral=True)
        
        related_case = None
        
        # Try to find case
        if case_id:
            async with AsyncSessionLocal() as db:
                stmt = select(ModCase).where(
                    ModCase.case_id == case_id,
                    ModCase.user_id == str(interaction.user.id)
                )
                result = await db.execute(stmt)
                mod_case = result.scalar_one_or_none()
                if mod_case:
                    related_case = mod_case.id
        
        description = f"**İtiraz Sebebi:** {reason}"
        if case_id:
            description += f"\n**Case ID:** {case_id}"
        
        ticket = await self._create_ticket(
            interaction,
            ticket_type=TicketType.APPEAL.value,
            title="Ceza İtirazı",
            description=description,
            related_case_id=related_case,
            priority=7
        )
        
        await self._send_to_queue(interaction, ticket)
        
        await interaction.followup.send(
            f"✅ İtirazınız alındı!\n"
            f"**Ticket ID:** `{ticket.ticket_id}`\n"
            f"Bir moderatör en kısa sürede inceleyecektir.",
            ephemeral=True
        )
    
    # ==================== STATUS COMMANDS ====================
    
    @app_commands.command(name="my-tickets", description="Açtığınız ticket'ları görüntüle")
    async def my_tickets(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            stmt = select(TicketV2).where(
                TicketV2.guild_id == str(interaction.guild_id),
                TicketV2.creator_id == str(interaction.user.id)
            ).order_by(TicketV2.created_at.desc()).limit(10)
            
            result = await db.execute(stmt)
            tickets = result.scalars().all()
        
        if not tickets:
            return await interaction.response.send_message("❌ Hiç ticket'ınız yok!", ephemeral=True)
        
        embed = discord.Embed(
            title="📋 Ticket'larınız",
            color=discord.Color.blurple()
        )
        
        status_emoji = {
            "opened": "📥",
            "triaged": "📋",
            "needs_info": "❓",
            "in_review": "🔍",
            "decided": "✅",
            "closed": "🔒"
        }
        
        for ticket in tickets:
            emoji = status_emoji.get(ticket.status, "📋")
            embed.add_field(
                name=f"{emoji} {ticket.ticket_id}",
                value=f"**Tür:** {ticket.ticket_type}\n**Durum:** {ticket.status}\n**Tarih:** <t:{int(ticket.created_at.timestamp())}:R>",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="my-cases", description="Moderation geçmişinizi görüntüle")
    async def my_cases(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            case_svc = CaseService(db)
            cases = await case_svc.get_user_cases(str(interaction.guild_id), str(interaction.user.id), 10)
        
        if not cases:
            return await interaction.response.send_message("✅ Hiç case kaydınız yok!", ephemeral=True)
        
        embed = discord.Embed(
            title="📋 Case Geçmişiniz",
            color=discord.Color.orange()
        )
        
        for case in cases:
            status = "✅" if case.status == "executed" else "🔄" if case.status == "appealed" else "↩️"
            embed.add_field(
                name=f"{status} {case.case_id}",
                value=f"**Kural:** {case.rule_id}\n**Aksiyon:** {case.action_type}\n**Tarih:** <t:{int(case.created_at.timestamp())}:R>",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ==================== MODERATOR COMMANDS ====================
    
    @app_commands.command(name="ticket-respond", description="Ticket'a yanıt ekle")
    @app_commands.describe(
        ticket_id="Ticket ID",
        response="Yanıtınız",
        internal="Sadece moderatörlere görünsün mü?"
    )
    async def ticket_respond(
        self,
        interaction: discord.Interaction,
        ticket_id: str,
        response: str,
        internal: bool = False
    ):
        async with AsyncSessionLocal() as db:
            governance_svc = GovernanceService(db)
            user_roles = [str(r.id) for r in interaction.user.roles]
            
            is_mod = (
                await governance_svc.is_triage(str(interaction.guild_id), user_roles) or
                await governance_svc.is_reviewer(str(interaction.guild_id), user_roles) or
                await governance_svc.is_ops_admin(str(interaction.guild_id), user_roles)
            )
            
            if not is_mod:
                return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)
            
            stmt = select(TicketV2).where(
                TicketV2.ticket_id == ticket_id,
                TicketV2.guild_id == str(interaction.guild_id)
            )
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return await interaction.response.send_message("❌ Ticket bulunamadı!", ephemeral=True)
            
            # Determine role
            if await governance_svc.is_reviewer(str(interaction.guild_id), user_roles):
                author_role = "reviewer"
            elif await governance_svc.is_triage(str(interaction.guild_id), user_roles):
                author_role = "triage"
            else:
                author_role = "opsadmin"
            
            message = TicketMessageV2(
                ticket_id=ticket.id,
                author_id=str(interaction.user.id),
                author_role=author_role,
                content=response,
                is_internal=internal
            )
            db.add(message)
            await db.commit()
        
        await interaction.response.send_message(
            f"✅ Yanıt eklendi (Ticket: {ticket_id})\n{'🔒 Internal' if internal else '📢 Public'}",
            ephemeral=True
        )
        
        # DM to user if not internal
        if not internal:
            try:
                user = await self.bot.fetch_user(int(ticket.creator_id))
                embed = discord.Embed(
                    title=f"📬 Ticket Yanıtı - {ticket_id}",
                    description=response,
                    color=discord.Color.blue()
                )
                await user.send(embed=embed)
            except:
                pass


async def setup(bot):
    await bot.add_cog(TicketsV2(bot))
