# (D) DATABASE ŞEMASI + ALEMBIC MİGRATION PLANI

## YENİ TABLOLAR

### 1. Governance Config
```sql
CREATE TABLE governance_configs (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) UNIQUE NOT NULL,
    
    -- Governance Mode
    governance_mode VARCHAR(20) DEFAULT 'bot_autocracy',  -- bot_autocracy, hybrid, manual
    owner_id VARCHAR(20),
    
    -- Sharding
    shard_id INTEGER,
    
    -- Lockdown Flags
    lockdown_active BOOLEAN DEFAULT FALSE,
    lockdown_started_at TIMESTAMP,
    lockdown_reason TEXT,
    
    -- Safe Mode
    safe_mode_active BOOLEAN DEFAULT FALSE,
    safe_mode_started_at TIMESTAMP,
    safe_mode_by VARCHAR(20),
    
    -- Thresholds
    raid_join_threshold INTEGER DEFAULT 15,
    raid_window_seconds INTEGER DEFAULT 60,
    newcomer_duration_hours INTEGER DEFAULT 24,
    newcomer_min_messages INTEGER DEFAULT 10,
    
    -- Retention
    evidence_retention_days INTEGER DEFAULT 90,
    audit_retention_days INTEGER DEFAULT 365,
    
    -- Slowmode
    auto_slowmode_enabled BOOLEAN DEFAULT TRUE,
    slowmode_heat_threshold FLOAT DEFAULT 0.7,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_guild FOREIGN KEY (guild_id) REFERENCES guilds(id)
);

CREATE INDEX idx_governance_guild ON governance_configs(guild_id);
```

### 2. Policies & Versions
```sql
CREATE TABLE policies (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    rule_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Policy Content (JSON)
    policy_json JSONB NOT NULL,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    priority INTEGER DEFAULT 500,
    created_by VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(guild_id, rule_id)
);

CREATE INDEX idx_policies_guild ON policies(guild_id);
CREATE INDEX idx_policies_active ON policies(guild_id, is_active);
CREATE INDEX idx_policies_priority ON policies(guild_id, priority DESC);

CREATE TABLE policy_versions (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER REFERENCES policies(id),
    version INTEGER NOT NULL,
    policy_json JSONB NOT NULL,
    changed_by VARCHAR(20),
    change_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_policy_versions ON policy_versions(policy_id, version);
```

### 3. User Risk Profiles
```sql
CREATE TABLE user_risk_profiles (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    user_id VARCHAR(20) NOT NULL,
    
    -- Static Factors
    account_age_days INTEGER,
    server_age_hours INTEGER,
    has_avatar BOOLEAN,
    
    -- Dynamic Scores
    base_risk_score FLOAT DEFAULT 0.0,
    current_risk_score FLOAT DEFAULT 0.0,
    
    -- Behavior Metrics (rolling 24h)
    messages_24h INTEGER DEFAULT 0,
    violations_24h INTEGER DEFAULT 0,
    warnings_24h INTEGER DEFAULT 0,
    
    -- Historical
    total_violations INTEGER DEFAULT 0,
    total_warnings INTEGER DEFAULT 0,
    total_timeouts INTEGER DEFAULT 0,
    total_kicks INTEGER DEFAULT 0,
    total_bans INTEGER DEFAULT 0,
    
    -- Appeal History
    appeals_submitted INTEGER DEFAULT 0,
    appeals_accepted INTEGER DEFAULT 0,
    appeals_rejected INTEGER DEFAULT 0,
    
    -- Status
    is_newcomer BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_quarantined BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    first_seen_at TIMESTAMP,
    last_message_at TIMESTAMP,
    last_violation_at TIMESTAMP,
    verified_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(guild_id, user_id)
);

CREATE INDEX idx_risk_guild_user ON user_risk_profiles(guild_id, user_id);
CREATE INDEX idx_risk_score ON user_risk_profiles(guild_id, current_risk_score DESC);
CREATE INDEX idx_risk_newcomer ON user_risk_profiles(guild_id, is_newcomer);
```

### 4. Events Ingested (Idempotency)
```sql
CREATE TABLE events_ingested (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,  -- hash of event data
    guild_id VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(20),
    channel_id VARCHAR(20),
    
    -- Processing Status
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,
    
    -- Metadata
    shard_id INTEGER,
    
    -- Partition by time
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE events_ingested_2026_01 PARTITION OF events_ingested
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE events_ingested_2026_02 PARTITION OF events_ingested
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... vb.

CREATE INDEX idx_events_event_id ON events_ingested(event_id);
CREATE INDEX idx_events_guild ON events_ingested(guild_id, created_at DESC);
```

### 5. Cases (Enhanced)
```sql
CREATE TABLE mod_cases (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(20) UNIQUE NOT NULL,  -- GUILD-XXXXX format
    guild_id VARCHAR(20) NOT NULL,
    user_id VARCHAR(20) NOT NULL,
    
    -- Rule Info
    rule_id VARCHAR(100),
    policy_version INTEGER,
    
    -- Scoring
    risk_score_at_time FLOAT,
    confidence FLOAT,  -- 0.0 - 1.0
    
    -- Action
    action_type VARCHAR(50) NOT NULL,  -- nudge, warn, delete, timeout, kick, ban
    action_duration_seconds INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'executed',  -- executed, appealed, overturned
    decided_by VARCHAR(20) DEFAULT 'bot',   -- 'bot' or user_id for overturns
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    expires_at TIMESTAMP,  -- for timeouts/tempbans
    
    -- Metadata
    channel_id VARCHAR(20),
    message_id VARCHAR(20),
    reason TEXT
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_cases_guild ON mod_cases(guild_id, created_at DESC);
CREATE INDEX idx_cases_user ON mod_cases(guild_id, user_id);
CREATE INDEX idx_cases_rule ON mod_cases(guild_id, rule_id);
CREATE INDEX idx_cases_status ON mod_cases(status);
```

### 6. Evidence
```sql
CREATE TABLE evidence (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT REFERENCES mod_cases(id),
    
    -- Content
    evidence_type VARCHAR(50) NOT NULL,  -- message, attachment, context, screenshot
    content_snippet TEXT,  -- max 500 chars
    content_hash VARCHAR(64),  -- SHA256
    
    -- Attachments
    attachment_url TEXT,
    attachment_type VARCHAR(50),
    
    -- Context Messages
    context_position INTEGER,  -- -3, -2, -1, 0, 1, 2, 3
    
    -- Metadata
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- for retention
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evidence_case ON evidence(case_id);
CREATE INDEX idx_evidence_expires ON evidence(expires_at);
```

### 7. Tickets V2 (Enhanced)
```sql
CREATE TABLE tickets_v2 (
    id BIGSERIAL PRIMARY KEY,
    ticket_id VARCHAR(20) UNIQUE NOT NULL,  -- GUILD-T-XXXXX
    guild_id VARCHAR(20) NOT NULL,
    
    -- Ticket Type
    ticket_type VARCHAR(20) NOT NULL,  -- report, complaint, request, appeal
    
    -- Participants
    creator_id VARCHAR(20) NOT NULL,
    subject_id VARCHAR(20),  -- reported user, or null
    assigned_to VARCHAR(20),  -- triage/reviewer
    
    -- Related Case
    related_case_id BIGINT REFERENCES mod_cases(id),
    
    -- Status
    status VARCHAR(20) DEFAULT 'opened',
    priority INTEGER DEFAULT 5,  -- 1-10, 10 highest
    
    -- Tags (JSON array)
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Content
    title VARCHAR(255),
    description TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triaged_at TIMESTAMP,
    decided_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- Resolution
    resolution VARCHAR(50),  -- approved, denied, duplicate, invalid
    resolution_reason TEXT
);

CREATE INDEX idx_tickets_guild ON tickets_v2(guild_id);
CREATE INDEX idx_tickets_status ON tickets_v2(guild_id, status);
CREATE INDEX idx_tickets_creator ON tickets_v2(creator_id);
CREATE INDEX idx_tickets_assigned ON tickets_v2(assigned_to);

CREATE TABLE ticket_messages_v2 (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT REFERENCES tickets_v2(id),
    author_id VARCHAR(20) NOT NULL,
    author_role VARCHAR(20),  -- user, triage, reviewer, bot
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,  -- hidden from ticket creator
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ticket_messages ON ticket_messages_v2(ticket_id);

CREATE TABLE ticket_tags (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7),
    description TEXT,
    UNIQUE(guild_id, name)
);
```

### 8. Actions (Discord Dispatch Log)
```sql
CREATE TABLE discord_actions (
    id BIGSERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    
    -- Action Details
    action_type VARCHAR(50) NOT NULL,
    target_user_id VARCHAR(20),
    target_channel_id VARCHAR(20),
    target_message_id VARCHAR(20),
    
    -- Source
    triggered_by VARCHAR(20) DEFAULT 'bot',
    case_id BIGINT REFERENCES mod_cases(id),
    
    -- Execution
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Discord Response
    discord_audit_id VARCHAR(20),
    
    -- Idempotency
    action_id VARCHAR(64) UNIQUE NOT NULL
) PARTITION BY RANGE (executed_at);

CREATE INDEX idx_actions_guild ON discord_actions(guild_id, executed_at DESC);
CREATE INDEX idx_actions_user ON discord_actions(target_user_id);
CREATE INDEX idx_actions_case ON discord_actions(case_id);
```

### 9. Audit Events
```sql
CREATE TABLE audit_events (
    id BIGSERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    
    -- Event Info
    event_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(20) NOT NULL,  -- bot or human
    actor_type VARCHAR(20),  -- bot, owner, opsadmin, triage, reviewer
    
    -- Target
    target_type VARCHAR(20),  -- user, channel, role, policy, ticket
    target_id VARCHAR(20),
    
    -- Details
    action VARCHAR(50) NOT NULL,
    details JSONB,
    
    -- Related
    case_id BIGINT,
    ticket_id BIGINT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_audit_guild ON audit_events(guild_id, created_at DESC);
CREATE INDEX idx_audit_actor ON audit_events(actor_id);
CREATE INDEX idx_audit_type ON audit_events(event_type);
```

### 10. Channel Heat Scores
```sql
CREATE TABLE channel_heat (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    channel_id VARCHAR(20) NOT NULL,
    
    -- Current Heat
    heat_score FLOAT DEFAULT 0.0,  -- 0.0 - 1.0
    
    -- Components
    message_rate FLOAT DEFAULT 0.0,
    toxicity_rate FLOAT DEFAULT 0.0,
    report_rate FLOAT DEFAULT 0.0,
    mod_action_rate FLOAT DEFAULT 0.0,
    
    -- Slowmode
    current_slowmode INTEGER DEFAULT 0,
    auto_slowmode_active BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    last_calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(guild_id, channel_id)
);

CREATE INDEX idx_heat_channel ON channel_heat(guild_id, channel_id);
CREATE INDEX idx_heat_score ON channel_heat(heat_score DESC);
```

---

## ALEMBIC MİGRATION

```python
# alembic/versions/xxx_bot_autocracy_mvp.py
"""Bot Autocracy MVP Tables

Revision ID: bot_autocracy_001
Revises: <previous_revision>
Create Date: 2026-01-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'bot_autocracy_001'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Governance Configs
    op.create_table(
        'governance_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.String(20), unique=True, nullable=False),
        sa.Column('governance_mode', sa.String(20), default='bot_autocracy'),
        sa.Column('owner_id', sa.String(20)),
        sa.Column('shard_id', sa.Integer()),
        sa.Column('lockdown_active', sa.Boolean(), default=False),
        sa.Column('lockdown_started_at', sa.DateTime()),
        sa.Column('lockdown_reason', sa.Text()),
        sa.Column('safe_mode_active', sa.Boolean(), default=False),
        sa.Column('safe_mode_started_at', sa.DateTime()),
        sa.Column('safe_mode_by', sa.String(20)),
        sa.Column('raid_join_threshold', sa.Integer(), default=15),
        sa.Column('raid_window_seconds', sa.Integer(), default=60),
        sa.Column('newcomer_duration_hours', sa.Integer(), default=24),
        sa.Column('newcomer_min_messages', sa.Integer(), default=10),
        sa.Column('evidence_retention_days', sa.Integer(), default=90),
        sa.Column('audit_retention_days', sa.Integer(), default=365),
        sa.Column('auto_slowmode_enabled', sa.Boolean(), default=True),
        sa.Column('slowmode_heat_threshold', sa.Float(), default=0.7),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_governance_guild', 'governance_configs', ['guild_id'])
    
    # 2. Policies
    op.create_table(
        'policies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('policy_json', JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('priority', sa.Integer(), default=500),
        sa.Column('created_by', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('guild_id', 'rule_id'),
    )
    op.create_index('idx_policies_guild', 'policies', ['guild_id'])
    op.create_index('idx_policies_active', 'policies', ['guild_id', 'is_active'])
    
    # 3. User Risk Profiles
    op.create_table(
        'user_risk_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(20), nullable=False),
        sa.Column('account_age_days', sa.Integer()),
        sa.Column('server_age_hours', sa.Integer()),
        sa.Column('has_avatar', sa.Boolean()),
        sa.Column('base_risk_score', sa.Float(), default=0.0),
        sa.Column('current_risk_score', sa.Float(), default=0.0),
        sa.Column('messages_24h', sa.Integer(), default=0),
        sa.Column('violations_24h', sa.Integer(), default=0),
        sa.Column('warnings_24h', sa.Integer(), default=0),
        sa.Column('total_violations', sa.Integer(), default=0),
        sa.Column('total_warnings', sa.Integer(), default=0),
        sa.Column('total_timeouts', sa.Integer(), default=0),
        sa.Column('total_kicks', sa.Integer(), default=0),
        sa.Column('total_bans', sa.Integer(), default=0),
        sa.Column('appeals_submitted', sa.Integer(), default=0),
        sa.Column('appeals_accepted', sa.Integer(), default=0),
        sa.Column('appeals_rejected', sa.Integer(), default=0),
        sa.Column('is_newcomer', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_quarantined', sa.Boolean(), default=False),
        sa.Column('first_seen_at', sa.DateTime()),
        sa.Column('last_message_at', sa.DateTime()),
        sa.Column('last_violation_at', sa.DateTime()),
        sa.Column('verified_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('guild_id', 'user_id'),
    )
    op.create_index('idx_risk_guild_user', 'user_risk_profiles', ['guild_id', 'user_id'])
    op.create_index('idx_risk_score', 'user_risk_profiles', ['guild_id', 'current_risk_score'])
    
    # 4. Mod Cases
    op.create_table(
        'mod_cases',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('case_id', sa.String(20), unique=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(20), nullable=False),
        sa.Column('rule_id', sa.String(100)),
        sa.Column('policy_version', sa.Integer()),
        sa.Column('risk_score_at_time', sa.Float()),
        sa.Column('confidence', sa.Float()),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_duration_seconds', sa.Integer()),
        sa.Column('status', sa.String(20), default='executed'),
        sa.Column('decided_by', sa.String(20), default='bot'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('channel_id', sa.String(20)),
        sa.Column('message_id', sa.String(20)),
        sa.Column('reason', sa.Text()),
    )
    op.create_index('idx_cases_guild', 'mod_cases', ['guild_id', 'created_at'])
    op.create_index('idx_cases_user', 'mod_cases', ['guild_id', 'user_id'])
    op.create_index('idx_cases_rule', 'mod_cases', ['guild_id', 'rule_id'])
    
    # 5. Evidence
    op.create_table(
        'evidence',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('case_id', sa.BigInteger(), sa.ForeignKey('mod_cases.id')),
        sa.Column('evidence_type', sa.String(50), nullable=False),
        sa.Column('content_snippet', sa.Text()),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('attachment_url', sa.Text()),
        sa.Column('attachment_type', sa.String(50)),
        sa.Column('context_position', sa.Integer()),
        sa.Column('captured_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_evidence_case', 'evidence', ['case_id'])
    
    # 6. Channel Heat
    op.create_table(
        'channel_heat',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('channel_id', sa.String(20), nullable=False),
        sa.Column('heat_score', sa.Float(), default=0.0),
        sa.Column('message_rate', sa.Float(), default=0.0),
        sa.Column('toxicity_rate', sa.Float(), default=0.0),
        sa.Column('report_rate', sa.Float(), default=0.0),
        sa.Column('mod_action_rate', sa.Float(), default=0.0),
        sa.Column('current_slowmode', sa.Integer(), default=0),
        sa.Column('auto_slowmode_active', sa.Boolean(), default=False),
        sa.Column('last_calculated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('guild_id', 'channel_id'),
    )
    op.create_index('idx_heat_channel', 'channel_heat', ['guild_id', 'channel_id'])


def downgrade():
    op.drop_table('channel_heat')
    op.drop_table('evidence')
    op.drop_table('mod_cases')
    op.drop_table('user_risk_profiles')
    op.drop_table('policies')
    op.drop_table('governance_configs')
```
