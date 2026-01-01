"""
Governance Service - Governance configuration management
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from lithium_core.models.governance import (
    GovernanceConfig, GovernanceMode, ChannelHeat
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("lithium-bot")


class GovernanceService:
    """Governance konfigürasyon yönetimi"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_config(self, guild_id: str) -> GovernanceConfig:
        """Guild config al veya oluştur"""
        stmt = select(GovernanceConfig).where(GovernanceConfig.guild_id == guild_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            config = GovernanceConfig(
                guild_id=guild_id,
                governance_mode=GovernanceMode.BOT_AUTOCRACY.value
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        
        return config
    
    async def update_config(
        self,
        guild_id: str,
        **kwargs
    ) -> GovernanceConfig:
        """Config güncelle"""
        config = await self.get_or_create_config(guild_id)
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    # ==================== SAFE MODE ====================
    
    async def enable_safe_mode(
        self,
        guild_id: str,
        activated_by: str,
        reason: str = None
    ) -> GovernanceConfig:
        """Safe mode aktive et"""
        config = await self.get_or_create_config(guild_id)
        
        config.safe_mode_active = True
        config.safe_mode_started_at = datetime.utcnow()
        config.safe_mode_by = activated_by
        
        await self.db.commit()
        logger.warning(f"Safe mode ENABLED for guild {guild_id} by {activated_by}")
        
        return config
    
    async def disable_safe_mode(self, guild_id: str) -> GovernanceConfig:
        """Safe mode deaktive et"""
        config = await self.get_or_create_config(guild_id)
        
        config.safe_mode_active = False
        config.safe_mode_started_at = None
        config.safe_mode_by = None
        
        await self.db.commit()
        logger.info(f"Safe mode DISABLED for guild {guild_id}")
        
        return config
    
    async def is_safe_mode(self, guild_id: str) -> bool:
        """Safe mode aktif mi?"""
        config = await self.get_or_create_config(guild_id)
        return config.safe_mode_active
    
    # ==================== LOCKDOWN ====================
    
    async def enable_lockdown(
        self,
        guild_id: str,
        reason: str,
        duration_seconds: int = 3600
    ) -> GovernanceConfig:
        """Lockdown aktive et"""
        config = await self.get_or_create_config(guild_id)
        
        config.lockdown_active = True
        config.lockdown_started_at = datetime.utcnow()
        config.lockdown_reason = reason
        config.lockdown_expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        await self.db.commit()
        logger.warning(f"Lockdown ENABLED for guild {guild_id}: {reason}")
        
        return config
    
    async def disable_lockdown(self, guild_id: str) -> GovernanceConfig:
        """Lockdown deaktive et"""
        config = await self.get_or_create_config(guild_id)
        
        config.lockdown_active = False
        config.lockdown_started_at = None
        config.lockdown_reason = None
        config.lockdown_expires_at = None
        
        await self.db.commit()
        logger.info(f"Lockdown DISABLED for guild {guild_id}")
        
        return config
    
    async def is_lockdown(self, guild_id: str) -> bool:
        """Lockdown aktif mi?"""
        config = await self.get_or_create_config(guild_id)
        
        if not config.lockdown_active:
            return False
        
        # Süre doldu mu?
        if config.lockdown_expires_at and config.lockdown_expires_at < datetime.utcnow():
            await self.disable_lockdown(guild_id)
            return False
        
        return True
    
    async def check_expired_lockdowns(self):
        """Süresi dolan lockdown'ları kaldır"""
        stmt = select(GovernanceConfig).where(
            GovernanceConfig.lockdown_active == True,
            GovernanceConfig.lockdown_expires_at <= datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        configs = result.scalars().all()
        
        for config in configs:
            config.lockdown_active = False
            config.lockdown_started_at = None
            config.lockdown_reason = None
            config.lockdown_expires_at = None
            logger.info(f"Lockdown expired for guild {config.guild_id}")
        
        await self.db.commit()
    
    # ==================== CHANNEL HEAT ====================
    
    async def get_or_create_heat(self, guild_id: str, channel_id: str) -> ChannelHeat:
        """Channel heat al veya oluştur"""
        stmt = select(ChannelHeat).where(
            ChannelHeat.guild_id == guild_id,
            ChannelHeat.channel_id == channel_id
        )
        result = await self.db.execute(stmt)
        heat = result.scalar_one_or_none()
        
        if not heat:
            heat = ChannelHeat(
                guild_id=guild_id,
                channel_id=channel_id
            )
            self.db.add(heat)
            await self.db.commit()
            await self.db.refresh(heat)
        
        return heat
    
    async def update_channel_heat(
        self,
        guild_id: str,
        channel_id: str,
        message_rate: float = None,
        toxicity_rate: float = None,
        report_rate: float = None,
        mod_action_rate: float = None
    ) -> ChannelHeat:
        """Channel heat güncelle"""
        heat = await self.get_or_create_heat(guild_id, channel_id)
        
        if message_rate is not None:
            heat.message_rate = message_rate
        if toxicity_rate is not None:
            heat.toxicity_rate = toxicity_rate
        if report_rate is not None:
            heat.report_rate = report_rate
        if mod_action_rate is not None:
            heat.mod_action_rate = mod_action_rate
        
        # Toplam heat skoru hesapla
        heat.heat_score = (
            heat.message_rate * 0.2 +
            heat.toxicity_rate * 0.4 +
            heat.report_rate * 0.2 +
            heat.mod_action_rate * 0.2
        )
        heat.heat_score = min(1.0, max(0.0, heat.heat_score))
        heat.last_calculated_at = datetime.utcnow()
        
        await self.db.commit()
        return heat
    
    async def get_hot_channels(
        self,
        guild_id: str,
        threshold: float = 0.5
    ) -> List[ChannelHeat]:
        """Sıcak kanalları getir"""
        stmt = select(ChannelHeat).where(
            ChannelHeat.guild_id == guild_id,
            ChannelHeat.heat_score >= threshold
        ).order_by(ChannelHeat.heat_score.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def should_auto_slowmode(
        self,
        guild_id: str,
        channel_id: str
    ) -> Optional[int]:
        """Otomatik slowmode gerekli mi? Dönüş: slowmode süresi veya None"""
        config = await self.get_or_create_config(guild_id)
        
        if not config.auto_slowmode_enabled:
            return None
        
        heat = await self.get_or_create_heat(guild_id, channel_id)
        
        if heat.heat_score < config.slowmode_heat_threshold:
            # Sıcaklık düşük, slowmode'u kaldır
            if heat.auto_slowmode_active:
                heat.auto_slowmode_active = False
                heat.current_slowmode = 0
                await self.db.commit()
                return 0
            return None
        
        # Sıcaklık yüksek, slowmode uygula
        if heat.heat_score >= 0.9:
            slowmode = 30  # 30 saniye
        elif heat.heat_score >= 0.8:
            slowmode = 20
        elif heat.heat_score >= 0.7:
            slowmode = 10
        else:
            slowmode = 5
        
        if heat.current_slowmode != slowmode:
            heat.current_slowmode = slowmode
            heat.auto_slowmode_active = True
            await self.db.commit()
            return slowmode
        
        return None
    
    # ==================== ROLE CHECKS ====================
    
    async def is_ops_admin(self, guild_id: str, user_roles: List[str]) -> bool:
        """Kullanıcı OpsAdmin mi?"""
        config = await self.get_or_create_config(guild_id)
        admin_roles = config.opsadmin_role_ids or []
        return any(role in admin_roles for role in user_roles)
    
    async def is_triage(self, guild_id: str, user_roles: List[str]) -> bool:
        """Kullanıcı Triage mi?"""
        config = await self.get_or_create_config(guild_id)
        triage_roles = config.triage_role_ids or []
        return any(role in triage_roles for role in user_roles)
    
    async def is_reviewer(self, guild_id: str, user_roles: List[str]) -> bool:
        """Kullanıcı Reviewer mi?"""
        config = await self.get_or_create_config(guild_id)
        reviewer_roles = config.reviewer_role_ids or []
        return any(role in reviewer_roles for role in user_roles)
    
    async def setup_governance_roles(
        self,
        guild_id: str,
        opsadmin_role_id: str = None,
        triage_role_id: str = None,
        reviewer_role_id: str = None,
        newcomer_role_id: str = None,
        verified_role_id: str = None,
        quarantine_role_id: str = None
    ) -> GovernanceConfig:
        """Governance rollerini ayarla"""
        config = await self.get_or_create_config(guild_id)
        
        if opsadmin_role_id:
            config.opsadmin_role_ids = [opsadmin_role_id]
        if triage_role_id:
            config.triage_role_ids = [triage_role_id]
        if reviewer_role_id:
            config.reviewer_role_ids = [reviewer_role_id]
        if newcomer_role_id:
            config.newcomer_role_id = newcomer_role_id
        if verified_role_id:
            config.verified_role_id = verified_role_id
        if quarantine_role_id:
            config.quarantine_role_id = quarantine_role_id
        
        await self.db.commit()
        return config
    
    async def setup_governance_channels(
        self,
        guild_id: str,
        mod_log_channel_id: str = None,
        audit_log_channel_id: str = None,
        alerts_channel_id: str = None,
        new_members_channel_id: str = None
    ) -> GovernanceConfig:
        """Governance kanallarını ayarla"""
        config = await self.get_or_create_config(guild_id)
        
        if mod_log_channel_id:
            config.mod_log_channel_id = mod_log_channel_id
        if audit_log_channel_id:
            config.audit_log_channel_id = audit_log_channel_id
        if alerts_channel_id:
            config.alerts_channel_id = alerts_channel_id
        if new_members_channel_id:
            config.new_members_channel_id = new_members_channel_id
        
        await self.db.commit()
        return config
