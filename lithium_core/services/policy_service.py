"""
Policy Service - Policy evaluation and management
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from lithium_core.models.governance import Policy, PolicyVersion
import re
import logging

logger = logging.getLogger("lithium-bot")


class PolicyMatch:
    """Policy match sonucu"""
    def __init__(self, policy: Policy, score: float, matched_conditions: List[str]):
        self.policy = policy
        self.score = score
        self.matched_conditions = matched_conditions
        self.rule_id = policy.rule_id
        self.actions = policy.policy_json.get("actions", {})
        self.risk_weight = policy.policy_json.get("risk_weight", 0.5)
        self.threshold = policy.policy_json.get("threshold", 0.5)


class PolicyService:
    """Policy yönetimi ve değerlendirme servisi"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._policy_cache: Dict[str, List[Policy]] = {}
    
    async def get_active_policies(self, guild_id: str) -> List[Policy]:
        """Aktif policy'leri cache'li olarak al"""
        if guild_id in self._policy_cache:
            return self._policy_cache[guild_id]
        
        stmt = select(Policy).where(
            Policy.guild_id == guild_id,
            Policy.is_active == True
        ).order_by(Policy.priority.desc())
        
        result = await self.db.execute(stmt)
        policies = result.scalars().all()
        
        self._policy_cache[guild_id] = list(policies)
        return self._policy_cache[guild_id]
    
    def invalidate_cache(self, guild_id: str = None):
        """Cache'i temizle"""
        if guild_id:
            self._policy_cache.pop(guild_id, None)
        else:
            self._policy_cache.clear()
    
    async def evaluate_message(
        self, 
        guild_id: str,
        user_id: str,
        content: str,
        channel_id: str,
        user_context: Dict[str, Any],
        message_context: Dict[str, Any]
    ) -> List[PolicyMatch]:
        """Mesajı tüm aktif policy'lere karşı değerlendir"""
        policies = await self.get_active_policies(guild_id)
        matches = []
        
        for policy in policies:
            match = self._evaluate_policy(
                policy, 
                "message", 
                content,
                channel_id,
                user_context,
                message_context
            )
            if match:
                matches.append(match)
        
        # En yüksek scorelu olanı önce döndür
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches
    
    async def evaluate_member_join(
        self,
        guild_id: str,
        user_id: str,
        user_context: Dict[str, Any]
    ) -> List[PolicyMatch]:
        """Yeni üye katılımını değerlendir"""
        policies = await self.get_active_policies(guild_id)
        matches = []
        
        for policy in policies:
            match = self._evaluate_policy(
                policy,
                "member_join",
                "",
                None,
                user_context,
                {}
            )
            if match:
                matches.append(match)
        
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches
    
    def _evaluate_policy(
        self,
        policy: Policy,
        event_type: str,
        content: str,
        channel_id: Optional[str],
        user_context: Dict[str, Any],
        message_context: Dict[str, Any]
    ) -> Optional[PolicyMatch]:
        """Tek bir policy'yi değerlendir"""
        policy_json = policy.policy_json
        
        # Event type kontrolü
        trigger = policy_json.get("trigger", {})
        event_types = trigger.get("event_types", [])
        if event_type not in event_types:
            return None
        
        # Channel exclude kontrolü
        exclude_channels = trigger.get("exclude_channels", [])
        if channel_id and channel_id in exclude_channels:
            return None
        
        # Exception kontrolü
        exceptions = policy_json.get("exceptions", {})
        exception_roles = exceptions.get("roles", [])
        user_roles = user_context.get("roles", [])
        if any(role in exception_roles for role in user_roles):
            return None
        
        exception_users = exceptions.get("users", [])
        if user_context.get("user_id") in exception_users:
            return None
        
        # Condition değerlendirme
        conditions = policy_json.get("conditions", {})
        matched_conditions = []
        total_score = 0.0
        condition_count = 0
        
        # Content patterns
        content_patterns = conditions.get("content_patterns", [])
        for pattern in content_patterns:
            if self._check_pattern(content, pattern):
                matched_conditions.append(f"pattern:{pattern.get('type')}")
                total_score += 1.0
                condition_count += 1
        
        # User criteria
        user_criteria = conditions.get("user_criteria", {})
        if user_criteria:
            user_match, user_conds = self._check_user_criteria(user_context, user_criteria)
            if user_match:
                matched_conditions.extend(user_conds)
                total_score += 0.5 * len(user_conds)
                condition_count += len(user_conds)
        
        # Content criteria
        content_criteria = conditions.get("content_criteria", {})
        if content_criteria and content:
            content_match, content_conds = self._check_content_criteria(content, message_context, content_criteria)
            if content_match:
                matched_conditions.extend(content_conds)
                total_score += 1.0 * len(content_conds)
                condition_count += len(content_conds)
        
        # Rate limit (bu harici olarak kontrol edilmeli)
        
        if not matched_conditions:
            return None
        
        # Score hesapla
        risk_weight = policy_json.get("risk_weight", 0.5)
        threshold = policy_json.get("threshold", 0.5)
        
        normalized_score = min(1.0, total_score / max(1, condition_count)) * risk_weight
        
        if normalized_score >= threshold:
            return PolicyMatch(policy, normalized_score, matched_conditions)
        
        return None
    
    def _check_pattern(self, content: str, pattern: Dict) -> bool:
        """Pattern kontrolü"""
        pattern_type = pattern.get("type")
        value = pattern.get("value", "")
        case_sensitive = pattern.get("case_sensitive", False)
        
        if not case_sensitive:
            content = content.lower()
            value = value.lower()
        
        if pattern_type == "keyword":
            return value in content
        
        elif pattern_type == "regex":
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(value, content, flags))
            except re.error:
                return False
        
        elif pattern_type == "domain":
            return value in content
        
        elif pattern_type == "fuzzy":
            # Basit fuzzy match
            return self._fuzzy_match(content, value)
        
        return False
    
    def _fuzzy_match(self, content: str, target: str, threshold: float = 0.8) -> bool:
        """Basit fuzzy matching"""
        # Levenshtein distance tabanlı basit implementasyon
        content_words = content.split()
        for word in content_words:
            if len(word) == 0:
                continue
            # Çok basit benzerlik
            common = sum(1 for c in target if c in word)
            similarity = common / max(len(target), len(word))
            if similarity >= threshold:
                return True
        return False
    
    def _check_user_criteria(
        self, 
        user_context: Dict[str, Any], 
        criteria: Dict
    ) -> tuple:
        """User criteria kontrolü"""
        matched = []
        
        if "account_age_days_lt" in criteria:
            if user_context.get("account_age_days", 999) < criteria["account_age_days_lt"]:
                matched.append("user:new_account")
        
        if "server_age_hours_lt" in criteria:
            if user_context.get("server_age_hours", 999) < criteria["server_age_hours_lt"]:
                matched.append("user:new_member")
        
        if "has_avatar" in criteria:
            if user_context.get("has_avatar", True) == criteria["has_avatar"]:
                matched.append("user:no_avatar")
        
        if "is_newcomer" in criteria:
            if user_context.get("is_newcomer", False) == criteria["is_newcomer"]:
                matched.append("user:newcomer")
        
        if "risk_score_gt" in criteria:
            if user_context.get("risk_score", 0) > criteria["risk_score_gt"]:
                matched.append("user:high_risk")
        
        return len(matched) > 0, matched
    
    def _check_content_criteria(
        self,
        content: str,
        message_context: Dict[str, Any],
        criteria: Dict
    ) -> tuple:
        """Content criteria kontrolü"""
        matched = []
        
        if "mention_count_gt" in criteria:
            mention_count = message_context.get("mention_count", 0)
            if mention_count > criteria["mention_count_gt"]:
                matched.append(f"content:mentions({mention_count})")
        
        if "link_count_gt" in criteria:
            link_count = message_context.get("link_count", 0)
            if link_count > criteria["link_count_gt"]:
                matched.append(f"content:links({link_count})")
        
        if "caps_percentage_gt" in criteria:
            if len(content) > 5:
                caps = sum(1 for c in content if c.isupper())
                letters = sum(1 for c in content if c.isalpha())
                if letters > 0:
                    percentage = (caps / letters) * 100
                    if percentage > criteria["caps_percentage_gt"]:
                        matched.append(f"content:caps({percentage:.0f}%)")
        
        if "emoji_flood_gt" in criteria:
            emoji_count = message_context.get("emoji_count", 0)
            if emoji_count > criteria["emoji_flood_gt"]:
                matched.append(f"content:emoji_flood({emoji_count})")
        
        if "zalgo_detected" in criteria and criteria["zalgo_detected"]:
            if self._detect_zalgo(content):
                matched.append("content:zalgo")
        
        return len(matched) > 0, matched
    
    def _detect_zalgo(self, text: str) -> bool:
        """Zalgo text detection"""
        # Combining characters range
        combining_count = sum(1 for char in text if '\u0300' <= char <= '\u036F')
        if len(text) > 0 and combining_count / len(text) > 0.3:
            return True
        return False
    
    # ==================== CRUD Operations ====================
    
    async def create_policy(
        self,
        guild_id: str,
        policy_json: Dict,
        created_by: str
    ) -> Policy:
        """Yeni policy oluştur"""
        policy = Policy(
            guild_id=guild_id,
            rule_id=policy_json.get("rule_id"),
            name=policy_json.get("name"),
            description=policy_json.get("description"),
            policy_json=policy_json,
            priority=policy_json.get("priority", 500),
            created_by=created_by
        )
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        
        self.invalidate_cache(guild_id)
        return policy
    
    async def update_policy(
        self,
        policy_id: int,
        policy_json: Dict,
        changed_by: str,
        change_reason: str = None
    ) -> Policy:
        """Policy güncelle ve versiyon kaydet"""
        stmt = select(Policy).where(Policy.id == policy_id)
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise ValueError("Policy not found")
        
        # Eski versiyonu kaydet
        version = PolicyVersion(
            policy_id=policy.id,
            version=policy.version,
            policy_json=policy.policy_json,
            changed_by=changed_by,
            change_reason=change_reason
        )
        self.db.add(version)
        
        # Güncelle
        policy.policy_json = policy_json
        policy.version += 1
        policy.name = policy_json.get("name", policy.name)
        policy.description = policy_json.get("description", policy.description)
        policy.priority = policy_json.get("priority", policy.priority)
        
        await self.db.commit()
        await self.db.refresh(policy)
        
        self.invalidate_cache(policy.guild_id)
        return policy
    
    async def toggle_policy(
        self,
        guild_id: str,
        rule_id: str,
        is_active: bool
    ) -> Optional[Policy]:
        """Policy aktif/pasif yap"""
        stmt = select(Policy).where(
            Policy.guild_id == guild_id,
            Policy.rule_id == rule_id
        )
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if policy:
            policy.is_active = is_active
            await self.db.commit()
            self.invalidate_cache(guild_id)
        
        return policy
