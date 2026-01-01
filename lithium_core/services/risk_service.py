"""
Risk Service - User risk scoring and management
"""
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from lithium_core.models.governance import UserRiskProfile, ModCase
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("lithium-bot")


class RiskScore:
    """Risk score sonucu"""
    def __init__(
        self, 
        base_score: float, 
        current_score: float, 
        components: Dict[str, float],
        is_high_risk: bool
    ):
        self.base_score = base_score
        self.current_score = current_score
        self.components = components
        self.is_high_risk = is_high_risk


class RiskService:
    """User risk scoring servisi"""
    
    # Risk ağırlıkları
    WEIGHTS = {
        "account_age": 0.15,
        "server_age": 0.10,
        "avatar": 0.05,
        "violations_24h": 0.25,
        "historical_violations": 0.20,
        "appeal_ratio": 0.10,
        "behavioral": 0.15
    }
    
    # Eşikler
    HIGH_RISK_THRESHOLD = 0.7
    DECAY_RATE_PER_HOUR = 0.01  # Saatte %1 azalma
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_profile(
        self, 
        guild_id: str, 
        user_id: str,
        account_created_at: datetime = None,
        joined_at: datetime = None,
        has_avatar: bool = True
    ) -> UserRiskProfile:
        """Kullanıcı profili al veya oluştur"""
        stmt = select(UserRiskProfile).where(
            UserRiskProfile.guild_id == guild_id,
            UserRiskProfile.user_id == user_id
        )
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            now = datetime.utcnow()
            
            account_age_days = None
            if account_created_at:
                account_age_days = (now - account_created_at).days
            
            server_age_hours = None
            if joined_at:
                server_age_hours = int((now - joined_at).total_seconds() / 3600)
            
            profile = UserRiskProfile(
                guild_id=guild_id,
                user_id=user_id,
                account_age_days=account_age_days,
                server_age_hours=server_age_hours,
                has_avatar=has_avatar,
                first_seen_at=now,
                is_newcomer=True
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        
        return profile
    
    async def calculate_risk_score(
        self,
        guild_id: str,
        user_id: str,
        profile: UserRiskProfile = None
    ) -> RiskScore:
        """Kullanıcı risk skorunu hesapla"""
        if not profile:
            profile = await self.get_or_create_profile(guild_id, user_id)
        
        components = {}
        
        # 1. Account Age Score (yeni hesap = yüksek risk)
        if profile.account_age_days is not None:
            if profile.account_age_days < 7:
                components["account_age"] = 0.9
            elif profile.account_age_days < 30:
                components["account_age"] = 0.5
            elif profile.account_age_days < 90:
                components["account_age"] = 0.2
            else:
                components["account_age"] = 0.0
        else:
            components["account_age"] = 0.3  # Bilinmiyor
        
        # 2. Server Age Score
        if profile.server_age_hours is not None:
            if profile.server_age_hours < 1:
                components["server_age"] = 0.9
            elif profile.server_age_hours < 24:
                components["server_age"] = 0.6
            elif profile.server_age_hours < 168:  # 1 hafta
                components["server_age"] = 0.3
            else:
                components["server_age"] = 0.0
        else:
            components["server_age"] = 0.5
        
        # 3. Avatar Score
        components["avatar"] = 0.5 if not profile.has_avatar else 0.0
        
        # 4. 24h Violations Score
        if profile.violations_24h > 0:
            components["violations_24h"] = min(1.0, profile.violations_24h * 0.25)
        else:
            components["violations_24h"] = 0.0
        
        # 5. Historical Violations Score
        total_hist = (
            profile.total_violations + 
            profile.total_warnings * 0.5 + 
            profile.total_timeouts * 1.5 + 
            profile.total_kicks * 2 + 
            profile.total_bans * 3
        )
        components["historical_violations"] = min(1.0, total_hist * 0.1)
        
        # 6. Appeal Ratio Score (çok appeal = düşük risk)
        if profile.appeals_submitted > 0:
            accept_ratio = profile.appeals_accepted / profile.appeals_submitted
            components["appeal_ratio"] = 1.0 - accept_ratio  # Kabul edilenler skoru düşürür
        else:
            components["appeal_ratio"] = 0.3  # Nötr
        
        # 7. Behavioral Score (son aktivite bazlı)
        if profile.last_violation_at:
            hours_since = (datetime.utcnow() - profile.last_violation_at).total_seconds() / 3600
            if hours_since < 1:
                components["behavioral"] = 0.9
            elif hours_since < 24:
                components["behavioral"] = 0.5
            else:
                components["behavioral"] = 0.1
        else:
            components["behavioral"] = 0.0
        
        # Ağırlıklı toplam
        weighted_score = sum(
            components.get(key, 0) * weight 
            for key, weight in self.WEIGHTS.items()
        )
        
        # Base score güncelle
        base_score = min(1.0, max(0.0, weighted_score))
        current_score = base_score  # Decay uygulanmış versiyon
        
        is_high_risk = current_score >= self.HIGH_RISK_THRESHOLD
        
        return RiskScore(
            base_score=base_score,
            current_score=current_score,
            components=components,
            is_high_risk=is_high_risk
        )
    
    async def update_after_violation(
        self,
        guild_id: str,
        user_id: str,
        violation_type: str,
        severity: float = 0.5
    ) -> UserRiskProfile:
        """Violation sonrası profil güncelle"""
        profile = await self.get_or_create_profile(guild_id, user_id)
        
        profile.violations_24h += 1
        profile.total_violations += 1
        profile.last_violation_at = datetime.utcnow()
        
        if violation_type == "warning":
            profile.warnings_24h += 1
            profile.total_warnings += 1
        elif violation_type == "timeout":
            profile.total_timeouts += 1
        elif violation_type == "kick":
            profile.total_kicks += 1
        elif violation_type == "ban":
            profile.total_bans += 1
        
        # Risk skorunu yeniden hesapla
        risk = await self.calculate_risk_score(guild_id, user_id, profile)
        profile.current_risk_score = risk.current_score
        profile.base_risk_score = risk.base_score
        
        await self.db.commit()
        return profile
    
    async def update_after_message(
        self,
        guild_id: str,
        user_id: str
    ) -> UserRiskProfile:
        """Mesaj sonrası profil güncelle"""
        profile = await self.get_or_create_profile(guild_id, user_id)
        
        profile.messages_24h += 1
        profile.last_message_at = datetime.utcnow()
        
        # Server age güncelle
        if profile.first_seen_at:
            profile.server_age_hours = int(
                (datetime.utcnow() - profile.first_seen_at).total_seconds() / 3600
            )
        
        await self.db.commit()
        return profile
    
    async def check_newcomer_promotion(
        self,
        guild_id: str,
        user_id: str,
        min_hours: int = 24,
        min_messages: int = 10
    ) -> bool:
        """Newcomer'ı verified'a yükseltme kontrolü"""
        profile = await self.get_or_create_profile(guild_id, user_id)
        
        if not profile.is_newcomer:
            return False  # Zaten verified
        
        if profile.is_quarantined:
            return False  # Karantinada
        
        if profile.violations_24h > 0:
            return False  # Son 24h ihlal var
        
        if (profile.server_age_hours or 0) < min_hours:
            return False
        
        if (profile.messages_24h or 0) < min_messages:
            return False
        
        # Promote!
        profile.is_newcomer = False
        profile.is_verified = True
        profile.verified_at = datetime.utcnow()
        
        await self.db.commit()
        return True
    
    async def quarantine_user(
        self,
        guild_id: str,
        user_id: str,
        reason: str = None
    ) -> UserRiskProfile:
        """Kullanıcıyı karantinaya al"""
        profile = await self.get_or_create_profile(guild_id, user_id)
        
        profile.is_quarantined = True
        profile.is_newcomer = True
        profile.is_verified = False
        profile.current_risk_score = 1.0  # Max risk
        
        await self.db.commit()
        return profile
    
    async def apply_decay(self):
        """Tüm kullanıcılara risk decay uygula (background task)"""
        stmt = select(UserRiskProfile).where(
            UserRiskProfile.current_risk_score > 0.0
        )
        result = await self.db.execute(stmt)
        profiles = result.scalars().all()
        
        for profile in profiles:
            # Decay uygula
            new_score = max(0.0, profile.current_risk_score - self.DECAY_RATE_PER_HOUR)
            profile.current_risk_score = new_score
            
            # 24h sayaçlarını sıfırla (eğer 24h geçtiyse)
            if profile.last_violation_at:
                hours_since = (datetime.utcnow() - profile.last_violation_at).total_seconds() / 3600
                if hours_since >= 24:
                    profile.violations_24h = 0
                    profile.warnings_24h = 0
        
        await self.db.commit()
        logger.info(f"Risk decay applied to {len(profiles)} profiles")
    
    def get_user_context(self, profile: UserRiskProfile) -> Dict[str, Any]:
        """Policy evaluation için user context oluştur"""
        return {
            "user_id": profile.user_id,
            "account_age_days": profile.account_age_days or 0,
            "server_age_hours": profile.server_age_hours or 0,
            "has_avatar": profile.has_avatar,
            "is_newcomer": profile.is_newcomer,
            "is_verified": profile.is_verified,
            "is_quarantined": profile.is_quarantined,
            "risk_score": profile.current_risk_score,
            "violations_24h": profile.violations_24h,
            "total_violations": profile.total_violations,
            "roles": []  # Dışarıdan doldurulmalı
        }
