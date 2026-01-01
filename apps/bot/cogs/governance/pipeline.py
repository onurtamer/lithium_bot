"""
Event Pipeline - Core event ingestion and processing
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.services.policy_service import PolicyService
from lithium_core.services.risk_service import RiskService
from lithium_core.services.case_service import CaseService
from lithium_core.services.governance_service import GovernanceService
from lithium_core.models.governance import EventIngested, GovernanceConfig
from sqlalchemy import select
import logging
import hashlib
import asyncio
import re
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import redis.asyncio as redis

logger = logging.getLogger("lithium-bot")


class EventPipeline(commands.Cog):
    """
    Event ingestion pipeline:
    1. Ingress (raw event)
    2. Normalization + enrichment
    3. Idempotency guard
    4. Rate check (noise governor)
    5. Risk scoring
    6. Policy evaluation
    7. Action dispatch or review queue
    8. Audit logging
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.redis: Optional[redis.Redis] = None
        self._processed_events: set = set()  # In-memory fallback
        self._rate_windows: Dict[str, list] = {}  # user_id -> [timestamps]
        
        # Start background tasks
        self.cleanup_processed_events.start()
        self.risk_decay_task.start()
    
    async def cog_load(self):
        """Initialize connections"""
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.redis = redis.from_url(redis_url)
            await self.redis.ping()
            logger.info("Redis connected for event pipeline")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory: {e}")
            self.redis = None
    
    def cog_unload(self):
        self.cleanup_processed_events.cancel()
        self.risk_decay_task.cancel()
    
    # ==================== HELPER METHODS ====================
    
    def _generate_event_id(self, event_type: str, guild_id: str, user_id: str, content_hash: str) -> str:
        """Generate unique event ID for idempotency"""
        data = f"{event_type}:{guild_id}:{user_id}:{content_hash}:{datetime.utcnow().isoformat()[:16]}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    async def _check_idempotency(self, event_id: str) -> bool:
        """Check if event already processed. Returns True if should skip."""
        if self.redis:
            result = await self.redis.get(f"event:{event_id}")
            if result:
                return True
            await self.redis.setex(f"event:{event_id}", 300, "1")  # 5 min TTL
            return False
        else:
            if event_id in self._processed_events:
                return True
            self._processed_events.add(event_id)
            return False
    
    async def _check_rate_limit(self, guild_id: str, user_id: str, limit: int = 7, window: int = 5) -> bool:
        """
        Check if user exceeds rate limit.
        Returns True if rate exceeded.
        """
        key = f"{guild_id}:{user_id}"
        now = datetime.utcnow()
        
        if self.redis:
            redis_key = f"rate:{key}"
            count = await self.redis.incr(redis_key)
            if count == 1:
                await self.redis.expire(redis_key, window)
            return count > limit
        else:
            if key not in self._rate_windows:
                self._rate_windows[key] = []
            
            # Clean old entries
            cutoff = now - timedelta(seconds=window)
            self._rate_windows[key] = [t for t in self._rate_windows[key] if t > cutoff]
            self._rate_windows[key].append(now)
            
            return len(self._rate_windows[key]) > limit
    
    def _extract_message_context(self, message: discord.Message) -> Dict[str, Any]:
        """Extract context from message for policy evaluation"""
        content = message.content
        
        # Count mentions
        mention_count = len(message.mentions) + len(message.role_mentions)
        if message.mention_everyone:
            mention_count += 1
        
        # Count links
        link_pattern = r'https?://[^\s]+'
        links = re.findall(link_pattern, content)
        link_count = len(links)
        
        # Count emojis
        emoji_pattern = r'<a?:\w+:\d+>|[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]'
        emojis = re.findall(emoji_pattern, content)
        emoji_count = len(emojis)
        
        # Content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return {
            "content": content,
            "content_hash": content_hash,
            "content_length": len(content),
            "mention_count": mention_count,
            "link_count": link_count,
            "emoji_count": emoji_count,
            "has_attachments": len(message.attachments) > 0,
            "attachment_count": len(message.attachments),
            "channel_id": str(message.channel.id),
            "message_id": str(message.id),
            "links": links
        }
    
    # ==================== EVENT HANDLERS ====================
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Main message event handler - pipeline entry point"""
        # Skip bots and DMs
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        
        try:
            async with AsyncSessionLocal() as db:
                # Initialize services
                governance_svc = GovernanceService(db)
                policy_svc = PolicyService(db)
                risk_svc = RiskService(db)
                case_svc = CaseService(db)
                
                # 1. Check safe mode
                if await governance_svc.is_safe_mode(guild_id):
                    # Safe mode: only log, no enforcement
                    await case_svc.log_audit_event(
                        guild_id=guild_id,
                        event_type="message",
                        actor_id=user_id,
                        action="logged_only",
                        details={"safe_mode": True, "content_length": len(message.content)}
                    )
                    return
                
                # 2. Extract message context
                msg_context = self._extract_message_context(message)
                
                # 3. Check idempotency
                event_id = self._generate_event_id("message", guild_id, user_id, msg_context["content_hash"])
                if await self._check_idempotency(event_id):
                    return
                
                # 4. Rate limit check (fast path)
                config = await governance_svc.get_or_create_config(guild_id)
                if await self._check_rate_limit(guild_id, user_id):
                    # Rate exceeded - immediate action
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, yavaşlayın lütfen!",
                            delete_after=5
                        )
                    except:
                        pass
                    
                    # Log case
                    case = await case_svc.create_case(
                        guild_id=guild_id,
                        user_id=user_id,
                        rule_id="rate_limit",
                        action_type="delete",
                        reason="Rate limit exceeded",
                        channel_id=str(message.channel.id),
                        message_id=str(message.id)
                    )
                    await case_svc.add_evidence(case.id, "message", message.content)
                    return
                
                # 5. Get/create user risk profile
                profile = await risk_svc.get_or_create_profile(
                    guild_id=guild_id,
                    user_id=user_id,
                    account_created_at=message.author.created_at,
                    joined_at=message.author.joined_at,
                    has_avatar=message.author.avatar is not None
                )
                
                # Update message count
                await risk_svc.update_after_message(guild_id, user_id)
                
                # 6. Build user context for policy
                user_context = risk_svc.get_user_context(profile)
                user_context["roles"] = [str(r.id) for r in message.author.roles]
                
                # 7. Evaluate policies
                matches = await policy_svc.evaluate_message(
                    guild_id=guild_id,
                    user_id=user_id,
                    content=message.content,
                    channel_id=str(message.channel.id),
                    user_context=user_context,
                    message_context=msg_context
                )
                
                if not matches:
                    # No policy match - update channel heat passively
                    await governance_svc.update_channel_heat(
                        guild_id, str(message.channel.id),
                        message_rate=0.1  # Slight increase
                    )
                    return
                
                # 8. Process top match
                top_match = matches[0]
                
                # Get actions
                actions = top_match.actions.get("immediate", [])
                should_review = top_match.actions.get("review_queue", False)
                
                if should_review or top_match.score < 0.7:
                    # Grey zone - send to review queue
                    # TODO: Create ticket for review
                    await case_svc.log_audit_event(
                        guild_id=guild_id,
                        event_type="policy_match_review",
                        actor_id="bot",
                        action="queue_review",
                        details={
                            "rule_id": top_match.rule_id,
                            "score": top_match.score,
                            "conditions": top_match.matched_conditions
                        }
                    )
                    return
                
                # 9. Execute actions
                for action in actions:
                    action_type = action.get("type")
                    
                    if action_type == "delete":
                        try:
                            await message.delete()
                        except discord.NotFound:
                            pass
                        except discord.Forbidden:
                            logger.warning(f"No permission to delete message in {message.channel.id}")
                    
                    elif action_type == "nudge":
                        nudge_msg = action.get("message", "Lütfen kurallara uyun.")
                        await message.channel.send(
                            f"💡 {message.author.mention}, {nudge_msg}",
                            delete_after=10
                        )
                    
                    elif action_type == "warn":
                        warn_msg = action.get("message", "Bu davranış kurallara aykırı.")
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, {warn_msg}",
                            delete_after=15
                        )
                        await risk_svc.update_after_violation(guild_id, user_id, "warning")
                    
                    elif action_type == "timeout":
                        duration = action.get("duration_seconds", 60)
                        try:
                            until = discord.utils.utcnow() + timedelta(seconds=duration)
                            await message.author.timeout(until, reason=f"Policy: {top_match.rule_id}")
                            
                            if action.get("dm_user"):
                                try:
                                    await message.author.send(
                                        f"⏰ {action.get('message', 'Kurallara aykırı davranış nedeniyle susturuldunuz.')}"
                                    )
                                except:
                                    pass
                            
                            await risk_svc.update_after_violation(guild_id, user_id, "timeout")
                        except discord.Forbidden:
                            logger.warning(f"No permission to timeout {user_id}")
                
                # 10. Create case
                case = await case_svc.create_case(
                    guild_id=guild_id,
                    user_id=user_id,
                    rule_id=top_match.rule_id,
                    action_type=actions[0].get("type") if actions else "log",
                    reason=f"Policy match: {top_match.matched_conditions}",
                    risk_score=top_match.score,
                    confidence=top_match.score,
                    channel_id=str(message.channel.id),
                    message_id=str(message.id)
                )
                
                # Add evidence
                await case_svc.add_evidence(case.id, "message", message.content)
                
                # 11. Update channel heat
                await governance_svc.update_channel_heat(
                    guild_id, str(message.channel.id),
                    toxicity_rate=0.3,
                    mod_action_rate=0.2
                )
                
                # 12. Log to mod-log channel
                if config.mod_log_channel_id:
                    log_channel = self.bot.get_channel(int(config.mod_log_channel_id))
                    if log_channel:
                        embed = discord.Embed(
                            title=f"📋 Case #{case.case_id}",
                            color=discord.Color.orange(),
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="Kullanıcı", value=f"{message.author.mention}", inline=True)
                        embed.add_field(name="Kural", value=top_match.rule_id, inline=True)
                        embed.add_field(name="Aksiyon", value=actions[0].get("type") if actions else "log", inline=True)
                        embed.add_field(name="Risk Skoru", value=f"{top_match.score:.2f}", inline=True)
                        embed.add_field(name="Koşullar", value=", ".join(top_match.matched_conditions)[:200], inline=False)
                        embed.set_footer(text=f"Kanal: #{message.channel.name}")
                        
                        await log_channel.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """New member event handler"""
        if member.bot:
            return
        
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        
        try:
            async with AsyncSessionLocal() as db:
                governance_svc = GovernanceService(db)
                risk_svc = RiskService(db)
                case_svc = CaseService(db)
                
                # Check lockdown
                if await governance_svc.is_lockdown(guild_id):
                    config = await governance_svc.get_or_create_config(guild_id)
                    
                    # Add newcomer role
                    if config.newcomer_role_id:
                        newcomer_role = member.guild.get_role(int(config.newcomer_role_id))
                        if newcomer_role:
                            await member.add_roles(newcomer_role, reason="Lockdown: newcomer restriction")
                    
                    # Log
                    await case_svc.log_audit_event(
                        guild_id=guild_id,
                        event_type="member_join_lockdown",
                        actor_id=user_id,
                        action="restricted",
                        details={"lockdown": True}
                    )
                    return
                
                # Create risk profile
                profile = await risk_svc.get_or_create_profile(
                    guild_id=guild_id,
                    user_id=user_id,
                    account_created_at=member.created_at,
                    joined_at=member.joined_at,
                    has_avatar=member.avatar is not None
                )
                
                # Calculate initial risk
                risk = await risk_svc.calculate_risk_score(guild_id, user_id, profile)
                
                # High risk check
                if risk.is_high_risk:
                    config = await governance_svc.get_or_create_config(guild_id)
                    
                    # Quarantine
                    if config.quarantine_role_id:
                        quarantine_role = member.guild.get_role(int(config.quarantine_role_id))
                        if quarantine_role:
                            await member.add_roles(quarantine_role, reason="High risk newcomer")
                            await risk_svc.quarantine_user(guild_id, user_id)
                    
                    # Alert
                    if config.alerts_channel_id:
                        alert_channel = self.bot.get_channel(int(config.alerts_channel_id))
                        if alert_channel:
                            embed = discord.Embed(
                                title="⚠️ Yüksek Riskli Yeni Üye",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow()
                            )
                            embed.add_field(name="Üye", value=f"{member.mention} ({member.id})", inline=False)
                            embed.add_field(name="Risk Skoru", value=f"{risk.current_score:.2f}", inline=True)
                            embed.add_field(name="Hesap Yaşı", value=f"{profile.account_age_days or '?'} gün", inline=True)
                            embed.add_field(name="Avatar", value="Var" if profile.has_avatar else "Yok", inline=True)
                            embed.set_thumbnail(url=member.display_avatar.url)
                            
                            await alert_channel.send(embed=embed)
                else:
                    # Normal newcomer
                    config = await governance_svc.get_or_create_config(guild_id)
                    if config.newcomer_role_id:
                        newcomer_role = member.guild.get_role(int(config.newcomer_role_id))
                        if newcomer_role:
                            await member.add_roles(newcomer_role, reason="New member")
        
        except Exception as e:
            logger.error(f"Member join pipeline error: {e}", exc_info=True)
    
    # ==================== BACKGROUND TASKS ====================
    
    @tasks.loop(minutes=5)
    async def cleanup_processed_events(self):
        """Clean up in-memory processed events"""
        if not self.redis:
            # Keep only last 1000 events
            if len(self._processed_events) > 1000:
                self._processed_events = set(list(self._processed_events)[-500:])
            
            # Clean rate windows
            now = datetime.utcnow()
            keys_to_delete = []
            for key, timestamps in self._rate_windows.items():
                self._rate_windows[key] = [t for t in timestamps if (now - t).seconds < 60]
                if not self._rate_windows[key]:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self._rate_windows[key]
    
    @cleanup_processed_events.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()
    
    @tasks.loop(hours=1)
    async def risk_decay_task(self):
        """Apply risk score decay"""
        async with AsyncSessionLocal() as db:
            risk_svc = RiskService(db)
            await risk_svc.apply_decay()
    
    @risk_decay_task.before_loop
    async def before_risk_decay(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(EventPipeline(bot))
