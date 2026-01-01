"""
Governance Models - Bot Autocracy Core
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, BigInteger, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from lithium_core.models.base import Base
from datetime import datetime
import enum


class GovernanceMode(str, enum.Enum):
    BOT_AUTOCRACY = "bot_autocracy"
    HYBRID = "hybrid"
    MANUAL = "manual"


class TicketType(str, enum.Enum):
    REPORT = "report"
    COMPLAINT = "complaint"
    REQUEST = "request"
    APPEAL = "appeal"


class TicketStatus(str, enum.Enum):
    OPENED = "opened"
    TRIAGED = "triaged"
    NEEDS_INFO = "needs_info"
    IN_REVIEW = "in_review"
    DECIDED = "decided"
    CLOSED = "closed"


class CaseStatus(str, enum.Enum):
    EXECUTED = "executed"
    APPEALED = "appealed"
    OVERTURNED = "overturned"


class ActionType(str, enum.Enum):
    NUDGE = "nudge"
    WARN = "warn"
    DELETE = "delete"
    TIMEOUT = "timeout"
    KICK = "kick"
    TEMPBAN = "tempban"
    BAN = "ban"
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    SLOWMODE = "slowmode"
    LOCKDOWN = "lockdown"


# ==================== GOVERNANCE CONFIG ====================

class GovernanceConfig(Base):
    __tablename__ = "governance_configs"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Governance Mode
    governance_mode = Column(String(20), default=GovernanceMode.BOT_AUTOCRACY.value)
    owner_id = Column(String(20))
    
    # Sharding
    shard_id = Column(Integer)
    
    # Lockdown Flags
    lockdown_active = Column(Boolean, default=False)
    lockdown_started_at = Column(DateTime)
    lockdown_reason = Column(Text)
    lockdown_expires_at = Column(DateTime)
    
    # Safe Mode
    safe_mode_active = Column(Boolean, default=False)
    safe_mode_started_at = Column(DateTime)
    safe_mode_by = Column(String(20))
    
    # Thresholds
    raid_join_threshold = Column(Integer, default=15)
    raid_window_seconds = Column(Integer, default=60)
    newcomer_duration_hours = Column(Integer, default=24)
    newcomer_min_messages = Column(Integer, default=10)
    
    # Retention
    evidence_retention_days = Column(Integer, default=90)
    audit_retention_days = Column(Integer, default=365)
    
    # Slowmode
    auto_slowmode_enabled = Column(Boolean, default=True)
    slowmode_heat_threshold = Column(Float, default=0.7)
    
    # Role IDs (JSON array)
    opsadmin_role_ids = Column(JSONB, default=list)
    triage_role_ids = Column(JSONB, default=list)
    reviewer_role_ids = Column(JSONB, default=list)
    newcomer_role_id = Column(String(20))
    verified_role_id = Column(String(20))
    quarantine_role_id = Column(String(20))
    
    # Channel IDs
    mod_log_channel_id = Column(String(20))
    audit_log_channel_id = Column(String(20))
    alerts_channel_id = Column(String(20))
    new_members_channel_id = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ==================== POLICIES ====================

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), nullable=False, index=True)
    rule_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Policy Content (JSON)
    policy_json = Column(JSONB, nullable=False)
    
    # Versioning
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    priority = Column(Integer, default=500, index=True)
    created_by = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    versions = relationship("PolicyVersion", back_populates="policy", lazy="dynamic")
    
    __table_args__ = (
        {"schema": None},
    )


class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    version = Column(Integer, nullable=False)
    policy_json = Column(JSONB, nullable=False)
    changed_by = Column(String(20))
    change_reason = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="versions")


# ==================== USER RISK PROFILES ====================

class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), nullable=False)
    user_id = Column(String(20), nullable=False)
    
    # Static Factors
    account_age_days = Column(Integer)
    server_age_hours = Column(Integer)
    has_avatar = Column(Boolean)
    
    # Dynamic Scores
    base_risk_score = Column(Float, default=0.0)
    current_risk_score = Column(Float, default=0.0, index=True)
    
    # Behavior Metrics (rolling 24h)
    messages_24h = Column(Integer, default=0)
    violations_24h = Column(Integer, default=0)
    warnings_24h = Column(Integer, default=0)
    
    # Historical
    total_violations = Column(Integer, default=0)
    total_warnings = Column(Integer, default=0)
    total_timeouts = Column(Integer, default=0)
    total_kicks = Column(Integer, default=0)
    total_bans = Column(Integer, default=0)
    
    # Appeal History
    appeals_submitted = Column(Integer, default=0)
    appeals_accepted = Column(Integer, default=0)
    appeals_rejected = Column(Integer, default=0)
    
    # Status
    is_newcomer = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    is_quarantined = Column(Boolean, default=False)
    
    # Timestamps
    first_seen_at = Column(DateTime)
    last_message_at = Column(DateTime)
    last_violation_at = Column(DateTime)
    verified_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        {"schema": None},
    )


# ==================== MOD CASES ====================

class ModCase(Base):
    __tablename__ = "mod_cases"
    
    id = Column(BigInteger, primary_key=True)
    case_id = Column(String(20), unique=True, nullable=False, index=True)
    guild_id = Column(String(20), nullable=False, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    
    # Rule Info
    rule_id = Column(String(100), index=True)
    policy_version = Column(Integer)
    
    # Scoring
    risk_score_at_time = Column(Float)
    confidence = Column(Float)  # 0.0 - 1.0
    
    # Action
    action_type = Column(String(50), nullable=False)
    action_duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(20), default=CaseStatus.EXECUTED.value)
    decided_by = Column(String(20), default="bot")  # 'bot' veya user_id
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    executed_at = Column(DateTime)
    expires_at = Column(DateTime)  # for timeouts/tempbans
    
    # Context
    channel_id = Column(String(20))
    message_id = Column(String(20))
    reason = Column(Text)
    
    # Relationships
    evidence = relationship("Evidence", back_populates="case", lazy="dynamic")
    tickets = relationship("TicketV2", back_populates="related_case", lazy="dynamic")


# ==================== EVIDENCE ====================

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(BigInteger, primary_key=True)
    case_id = Column(BigInteger, ForeignKey("mod_cases.id"), index=True)
    
    # Content
    evidence_type = Column(String(50), nullable=False)  # message, attachment, context, screenshot
    content_snippet = Column(Text)  # max 500 chars
    content_hash = Column(String(64))  # SHA256
    
    # Attachments
    attachment_url = Column(Text)
    attachment_type = Column(String(50))
    
    # Context Messages
    context_position = Column(Integer)  # -3, -2, -1, 0, 1, 2, 3
    
    # Metadata
    captured_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, index=True)  # for retention
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    case = relationship("ModCase", back_populates="evidence")


# ==================== TICKETS V2 ====================

class TicketV2(Base):
    __tablename__ = "tickets_v2"
    
    id = Column(BigInteger, primary_key=True)
    ticket_id = Column(String(20), unique=True, nullable=False, index=True)
    guild_id = Column(String(20), nullable=False, index=True)
    
    # Ticket Type
    ticket_type = Column(String(20), nullable=False)  # report, complaint, request, appeal
    
    # Participants
    creator_id = Column(String(20), nullable=False, index=True)
    subject_id = Column(String(20))  # reported user, or null
    assigned_to = Column(String(20), index=True)  # triage/reviewer
    
    # Related Case
    related_case_id = Column(BigInteger, ForeignKey("mod_cases.id"))
    
    # Status
    status = Column(String(20), default=TicketStatus.OPENED.value, index=True)
    priority = Column(Integer, default=5)  # 1-10, 10 highest
    
    # Tags (JSON array)
    tags = Column(JSONB, default=list)
    
    # Content
    title = Column(String(255))
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    triaged_at = Column(DateTime)
    decided_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Resolution
    resolution = Column(String(50))  # approved, denied, duplicate, invalid
    resolution_reason = Column(Text)
    
    # Relationships
    related_case = relationship("ModCase", back_populates="tickets")
    messages = relationship("TicketMessageV2", back_populates="ticket", lazy="dynamic")


class TicketMessageV2(Base):
    __tablename__ = "ticket_messages_v2"
    
    id = Column(BigInteger, primary_key=True)
    ticket_id = Column(BigInteger, ForeignKey("tickets_v2.id"), nullable=False, index=True)
    author_id = Column(String(20), nullable=False)
    author_role = Column(String(20))  # user, triage, reviewer, bot
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # hidden from ticket creator
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    ticket = relationship("TicketV2", back_populates="messages")


class TicketTag(Base):
    __tablename__ = "ticket_tags"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7))  # hex color
    description = Column(Text)
    
    __table_args__ = (
        {"schema": None},
    )


# ==================== CHANNEL HEAT ====================

class ChannelHeat(Base):
    __tablename__ = "channel_heat"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), nullable=False)
    channel_id = Column(String(20), nullable=False)
    
    # Current Heat
    heat_score = Column(Float, default=0.0, index=True)  # 0.0 - 1.0
    
    # Components
    message_rate = Column(Float, default=0.0)
    toxicity_rate = Column(Float, default=0.0)
    report_rate = Column(Float, default=0.0)
    mod_action_rate = Column(Float, default=0.0)
    
    # Slowmode
    current_slowmode = Column(Integer, default=0)
    auto_slowmode_active = Column(Boolean, default=False)
    
    # Timestamps
    last_calculated_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        {"schema": None},
    )


# ==================== EVENTS INGESTED (IDEMPOTENCY) ====================

class EventIngested(Base):
    __tablename__ = "events_ingested"
    
    id = Column(BigInteger, primary_key=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    guild_id = Column(String(20), nullable=False)
    event_type = Column(String(50), nullable=False)
    user_id = Column(String(20))
    channel_id = Column(String(20))
    
    # Processing Status
    processed_at = Column(DateTime, server_default=func.now())
    processing_time_ms = Column(Integer)
    
    # Metadata
    shard_id = Column(Integer)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)


# ==================== DISCORD ACTIONS LOG ====================

class DiscordAction(Base):
    __tablename__ = "discord_actions"
    
    id = Column(BigInteger, primary_key=True)
    guild_id = Column(String(20), nullable=False, index=True)
    
    # Action Details
    action_type = Column(String(50), nullable=False)
    target_user_id = Column(String(20), index=True)
    target_channel_id = Column(String(20))
    target_message_id = Column(String(20))
    
    # Source
    triggered_by = Column(String(20), default="bot")
    case_id = Column(BigInteger, ForeignKey("mod_cases.id"))
    
    # Execution
    executed_at = Column(DateTime, server_default=func.now(), index=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Discord Response
    discord_audit_id = Column(String(20))
    
    # Idempotency
    action_id = Column(String(64), unique=True, nullable=False)


# ==================== AUDIT EVENTS ====================

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(BigInteger, primary_key=True)
    guild_id = Column(String(20), nullable=False, index=True)
    
    # Event Info
    event_type = Column(String(50), nullable=False, index=True)
    actor_id = Column(String(20), nullable=False, index=True)  # bot or human
    actor_type = Column(String(20))  # bot, owner, opsadmin, triage, reviewer
    
    # Target
    target_type = Column(String(20))  # user, channel, role, policy, ticket
    target_id = Column(String(20))
    
    # Details
    action = Column(String(50), nullable=False)
    details = Column(JSONB)
    
    # Related
    case_id = Column(BigInteger)
    ticket_id = Column(BigInteger)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
