"""
Case Service - Moderation case management
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from lithium_core.models.governance import (
    ModCase, Evidence, CaseStatus, ActionType,
    DiscordAction, AuditEvent
)
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger("lithium-bot")


class CaseService:
    """Moderation case yönetimi"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _generate_case_id(self, guild_id: str) -> str:
        """Benzersiz case ID oluştur"""
        # Format: GUILD_PREFIX-XXXXX
        stmt = select(func.count(ModCase.id)).where(ModCase.guild_id == guild_id)
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        
        return f"{guild_id[-4:]}-{count + 1:05d}"
    
    async def create_case(
        self,
        guild_id: str,
        user_id: str,
        rule_id: str,
        action_type: str,
        reason: str,
        risk_score: float = None,
        confidence: float = None,
        channel_id: str = None,
        message_id: str = None,
        action_duration: int = None,
        policy_version: int = None,
        decided_by: str = "bot"
    ) -> ModCase:
        """Yeni case oluştur"""
        case_id = await self._generate_case_id(guild_id)
        
        case = ModCase(
            case_id=case_id,
            guild_id=guild_id,
            user_id=user_id,
            rule_id=rule_id,
            policy_version=policy_version,
            risk_score_at_time=risk_score,
            confidence=confidence,
            action_type=action_type,
            action_duration_seconds=action_duration,
            status=CaseStatus.EXECUTED.value,
            decided_by=decided_by,
            executed_at=datetime.utcnow(),
            channel_id=channel_id,
            message_id=message_id,
            reason=reason
        )
        
        # Expires hesapla (timeout/tempban için)
        if action_duration and action_type in ["timeout", "tempban"]:
            case.expires_at = datetime.utcnow() + timedelta(seconds=action_duration)
        
        self.db.add(case)
        await self.db.commit()
        await self.db.refresh(case)
        
        logger.info(f"Case created: {case_id} for user {user_id} in guild {guild_id}")
        return case
    
    async def add_evidence(
        self,
        case_id: int,
        evidence_type: str,
        content: str = None,
        attachment_url: str = None,
        attachment_type: str = None,
        context_position: int = None,
        retention_days: int = 90
    ) -> Evidence:
        """Case'e evidence ekle"""
        content_snippet = None
        content_hash = None
        
        if content:
            # Snippet (max 500 karakter)
            content_snippet = content[:500]
            # Hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        evidence = Evidence(
            case_id=case_id,
            evidence_type=evidence_type,
            content_snippet=content_snippet,
            content_hash=content_hash,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
            context_position=context_position,
            expires_at=datetime.utcnow() + timedelta(days=retention_days)
        )
        
        self.db.add(evidence)
        await self.db.commit()
        await self.db.refresh(evidence)
        
        return evidence
    
    async def get_case(self, case_id: str) -> Optional[ModCase]:
        """Case al"""
        stmt = select(ModCase).where(ModCase.case_id == case_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_cases(
        self,
        guild_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[ModCase]:
        """Kullanıcının case'lerini al"""
        stmt = select(ModCase).where(
            ModCase.guild_id == guild_id,
            ModCase.user_id == user_id
        ).order_by(ModCase.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_recent_cases(
        self,
        guild_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[ModCase]:
        """Son X saatteki case'leri al"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(ModCase).where(
            ModCase.guild_id == guild_id,
            ModCase.created_at >= since
        ).order_by(ModCase.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def overturn_case(
        self,
        case_id: str,
        overturned_by: str,
        reason: str
    ) -> Optional[ModCase]:
        """Case'i geri al (overturn)"""
        case = await self.get_case(case_id)
        if not case:
            return None
        
        case.status = CaseStatus.OVERTURNED.value
        case.decided_by = overturned_by
        case.reason = f"OVERTURNED: {reason}\nOriginal: {case.reason}"
        
        await self.db.commit()
        
        # Audit event oluştur
        await self.log_audit_event(
            guild_id=case.guild_id,
            event_type="case_overturn",
            actor_id=overturned_by,
            actor_type="reviewer",
            target_type="case",
            target_id=case.case_id,
            action="overturn",
            details={"reason": reason},
            case_id=case.id
        )
        
        logger.info(f"Case {case_id} overturned by {overturned_by}")
        return case
    
    async def mark_appealed(self, case_id: str) -> Optional[ModCase]:
        """Case'i appealed olarak işaretle"""
        case = await self.get_case(case_id)
        if not case:
            return None
        
        case.status = CaseStatus.APPEALED.value
        await self.db.commit()
        
        return case
    
    # ==================== DISCORD ACTIONS ====================
    
    async def log_discord_action(
        self,
        guild_id: str,
        action_type: str,
        target_user_id: str = None,
        target_channel_id: str = None,
        target_message_id: str = None,
        case_id: int = None,
        triggered_by: str = "bot",
        success: bool = True,
        error_message: str = None,
        discord_audit_id: str = None
    ) -> DiscordAction:
        """Discord API aksiyonunu logla"""
        # Idempotency key
        action_id = hashlib.sha256(
            f"{guild_id}:{action_type}:{target_user_id or ''}:{target_message_id or ''}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:32]
        
        action = DiscordAction(
            guild_id=guild_id,
            action_type=action_type,
            target_user_id=target_user_id,
            target_channel_id=target_channel_id,
            target_message_id=target_message_id,
            triggered_by=triggered_by,
            case_id=case_id,
            success=success,
            error_message=error_message,
            discord_audit_id=discord_audit_id,
            action_id=action_id
        )
        
        self.db.add(action)
        await self.db.commit()
        
        return action
    
    async def check_action_exists(self, action_id: str) -> bool:
        """Aksiyon zaten uygulandı mı kontrol et (idempotency)"""
        stmt = select(DiscordAction).where(DiscordAction.action_id == action_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    # ==================== AUDIT EVENTS ====================
    
    async def log_audit_event(
        self,
        guild_id: str,
        event_type: str,
        actor_id: str,
        action: str,
        actor_type: str = "bot",
        target_type: str = None,
        target_id: str = None,
        details: Dict = None,
        case_id: int = None,
        ticket_id: int = None
    ) -> AuditEvent:
        """Audit event oluştur"""
        event = AuditEvent(
            guild_id=guild_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            target_type=target_type,
            target_id=target_id,
            action=action,
            details=details or {},
            case_id=case_id,
            ticket_id=ticket_id
        )
        
        self.db.add(event)
        await self.db.commit()
        
        return event
    
    # ==================== STATISTICS ====================
    
    async def get_rule_stats(
        self,
        guild_id: str,
        hours: int = 24
    ) -> Dict[str, int]:
        """Kural bazlı istatistikler"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(
            ModCase.rule_id,
            func.count(ModCase.id).label("count")
        ).where(
            ModCase.guild_id == guild_id,
            ModCase.created_at >= since
        ).group_by(ModCase.rule_id)
        
        result = await self.db.execute(stmt)
        return {row.rule_id: row.count for row in result}
    
    async def get_action_stats(
        self,
        guild_id: str,
        hours: int = 24
    ) -> Dict[str, int]:
        """Aksiyon bazlı istatistikler"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(
            ModCase.action_type,
            func.count(ModCase.id).label("count")
        ).where(
            ModCase.guild_id == guild_id,
            ModCase.created_at >= since
        ).group_by(ModCase.action_type)
        
        result = await self.db.execute(stmt)
        return {row.action_type: row.count for row in result}
    
    async def get_false_positive_rate(
        self,
        guild_id: str,
        days: int = 7
    ) -> float:
        """False positive oranını hesapla"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Toplam case
        total_stmt = select(func.count(ModCase.id)).where(
            ModCase.guild_id == guild_id,
            ModCase.created_at >= since
        )
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        if total == 0:
            return 0.0
        
        # Overturned case
        overturned_stmt = select(func.count(ModCase.id)).where(
            ModCase.guild_id == guild_id,
            ModCase.created_at >= since,
            ModCase.status == CaseStatus.OVERTURNED.value
        )
        overturned_result = await self.db.execute(overturned_stmt)
        overturned = overturned_result.scalar() or 0
        
        return overturned / total
    
    async def cleanup_expired_evidence(self) -> int:
        """Süresi dolmuş evidence'ları sil"""
        stmt = select(Evidence).where(
            Evidence.expires_at <= datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        expired = result.scalars().all()
        
        count = len(expired)
        for evidence in expired:
            await self.db.delete(evidence)
        
        await self.db.commit()
        logger.info(f"Cleaned up {count} expired evidence records")
        
        return count
