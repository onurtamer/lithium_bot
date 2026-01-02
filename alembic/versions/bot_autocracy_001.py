"""Bot Autocracy Tables - Governance, Policies, Risk, Cases

Revision ID: 4e1d9b3a5c2f
Revises: 7bd60a5ba720
Create Date: 2026-01-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '4e1d9b3a5c2f'
down_revision = '7bd60a5ba720' # add_log_route
branch_labels = None
depends_on = None


def upgrade():
    # 1. Governance Configs
    op.create_table(
        'governance_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), unique=True, nullable=False),
        sa.Column('governance_mode', sa.String(20), server_default='bot_autocracy'),
        sa.Column('owner_id', sa.BigInteger()),
        sa.Column('shard_id', sa.Integer()),
        sa.Column('lockdown_active', sa.Boolean(), server_default='false'),
        sa.Column('lockdown_started_at', sa.DateTime()),
        sa.Column('lockdown_reason', sa.Text()),
        sa.Column('lockdown_expires_at', sa.DateTime()),
        sa.Column('safe_mode_active', sa.Boolean(), server_default='false'),
        sa.Column('safe_mode_started_at', sa.DateTime()),
        sa.Column('safe_mode_by', sa.BigInteger()),
        sa.Column('raid_join_threshold', sa.Integer(), server_default='15'),
        sa.Column('raid_window_seconds', sa.Integer(), server_default='60'),
        sa.Column('newcomer_duration_hours', sa.Integer(), server_default='24'),
        sa.Column('newcomer_min_messages', sa.Integer(), server_default='10'),
        sa.Column('evidence_retention_days', sa.Integer(), server_default='90'),
        sa.Column('audit_retention_days', sa.Integer(), server_default='365'),
        sa.Column('auto_slowmode_enabled', sa.Boolean(), server_default='true'),
        sa.Column('slowmode_heat_threshold', sa.Float(), server_default='0.7'),
        sa.Column('opsadmin_role_ids', JSONB(), server_default='[]'),
        sa.Column('triage_role_ids', JSONB(), server_default='[]'),
        sa.Column('reviewer_role_ids', JSONB(), server_default='[]'),
        sa.Column('newcomer_role_id', sa.BigInteger()),
        sa.Column('verified_role_id', sa.BigInteger()),
        sa.Column('quarantine_role_id', sa.BigInteger()),
        sa.Column('mod_log_channel_id', sa.BigInteger()),
        sa.Column('audit_log_channel_id', sa.BigInteger()),
        sa.Column('alerts_channel_id', sa.BigInteger()),
        sa.Column('new_members_channel_id', sa.BigInteger()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_governance_guild', 'governance_configs', ['guild_id'])

    # 2. Policies
    op.create_table(
        'policies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('policy_json', JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('priority', sa.Integer(), server_default='500'),
        sa.Column('created_by', sa.BigInteger()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('guild_id', 'rule_id', name='uq_policy_guild_rule'),
    )
    op.create_index('idx_policies_guild', 'policies', ['guild_id'])
    op.create_index('idx_policies_active', 'policies', ['guild_id', 'is_active'])
    op.create_index('idx_policies_priority', 'policies', ['priority'])

    # 3. Policy Versions
    op.create_table(
        'policy_versions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('policies.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('policy_json', JSONB(), nullable=False),
        sa.Column('changed_by', sa.BigInteger()),
        sa.Column('change_reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_policy_versions', 'policy_versions', ['policy_id', 'version'])

    # 4. User Risk Profiles
    op.create_table(
        'user_risk_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('account_age_days', sa.Integer()),
        sa.Column('server_age_hours', sa.Integer()),
        sa.Column('has_avatar', sa.Boolean()),
        sa.Column('base_risk_score', sa.Float(), server_default='0.0'),
        sa.Column('current_risk_score', sa.Float(), server_default='0.0'),
        sa.Column('messages_24h', sa.Integer(), server_default='0'),
        sa.Column('violations_24h', sa.Integer(), server_default='0'),
        sa.Column('warnings_24h', sa.Integer(), server_default='0'),
        sa.Column('total_violations', sa.Integer(), server_default='0'),
        sa.Column('total_warnings', sa.Integer(), server_default='0'),
        sa.Column('total_timeouts', sa.Integer(), server_default='0'),
        sa.Column('total_kicks', sa.Integer(), server_default='0'),
        sa.Column('total_bans', sa.Integer(), server_default='0'),
        sa.Column('appeals_submitted', sa.Integer(), server_default='0'),
        sa.Column('appeals_accepted', sa.Integer(), server_default='0'),
        sa.Column('appeals_rejected', sa.Integer(), server_default='0'),
        sa.Column('is_newcomer', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('is_quarantined', sa.Boolean(), server_default='false'),
        sa.Column('first_seen_at', sa.DateTime()),
        sa.Column('last_message_at', sa.DateTime()),
        sa.Column('last_violation_at', sa.DateTime()),
        sa.Column('verified_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('guild_id', 'user_id', name='uq_risk_profile'),
    )
    op.create_index('idx_risk_guild_user', 'user_risk_profiles', ['guild_id', 'user_id'])
    op.create_index('idx_risk_score', 'user_risk_profiles', ['guild_id', 'current_risk_score'])
    op.create_index('idx_risk_newcomer', 'user_risk_profiles', ['guild_id', 'is_newcomer'])

    # 5. Mod Cases
    op.create_table(
        'mod_cases',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('case_id', sa.String(20), unique=True, nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('rule_id', sa.String(100)),
        sa.Column('policy_version', sa.Integer()),
        sa.Column('risk_score_at_time', sa.Float()),
        sa.Column('confidence', sa.Float()),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_duration_seconds', sa.Integer()),
        sa.Column('status', sa.String(20), server_default='executed'),
        sa.Column('decided_by', sa.String(20), server_default='bot'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('channel_id', sa.BigInteger()),
        sa.Column('message_id', sa.BigInteger()),
        sa.Column('reason', sa.Text()),
    )
    op.create_index('idx_cases_guild', 'mod_cases', ['guild_id', 'created_at'])
    op.create_index('idx_cases_user', 'mod_cases', ['guild_id', 'user_id'])
    op.create_index('idx_cases_rule', 'mod_cases', ['guild_id', 'rule_id'])
    op.create_index('idx_cases_status', 'mod_cases', ['status'])

    # 6. Evidence
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
    op.create_index('idx_evidence_expires', 'evidence', ['expires_at'])

    # 7. Tickets V2
    op.create_table(
        'tickets_v2',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('ticket_id', sa.String(20), unique=True, nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('ticket_type', sa.String(20), nullable=False),
        sa.Column('creator_id', sa.BigInteger(), nullable=False),
        sa.Column('subject_id', sa.BigInteger()),
        sa.Column('assigned_to', sa.BigInteger()),
        sa.Column('related_case_id', sa.BigInteger(), sa.ForeignKey('mod_cases.id')),
        sa.Column('status', sa.String(20), server_default='opened'),
        sa.Column('priority', sa.Integer(), server_default='5'),
        sa.Column('tags', JSONB(), server_default='[]'),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('triaged_at', sa.DateTime()),
        sa.Column('decided_at', sa.DateTime()),
        sa.Column('closed_at', sa.DateTime()),
        sa.Column('resolution', sa.String(50)),
        sa.Column('resolution_reason', sa.Text()),
    )
    op.create_index('idx_tickets_guild', 'tickets_v2', ['guild_id'])
    op.create_index('idx_tickets_status', 'tickets_v2', ['guild_id', 'status'])
    op.create_index('idx_tickets_creator', 'tickets_v2', ['creator_id'])
    op.create_index('idx_tickets_assigned', 'tickets_v2', ['assigned_to'])

    # 8. Ticket Messages V2
    op.create_table(
        'ticket_messages_v2',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('ticket_id', sa.BigInteger(), sa.ForeignKey('tickets_v2.id'), nullable=False),
        sa.Column('author_id', sa.BigInteger(), nullable=False),
        sa.Column('author_role', sa.String(20)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_ticket_messages', 'ticket_messages_v2', ['ticket_id'])

    # 9. Ticket Tags
    op.create_table(
        'ticket_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('color', sa.String(7)),
        sa.Column('description', sa.Text()),
        sa.UniqueConstraint('guild_id', 'name', name='uq_ticket_tag'),
    )

    # 10. Channel Heat
    op.create_table(
        'channel_heat',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('heat_score', sa.Float(), server_default='0.0'),
        sa.Column('message_rate', sa.Float(), server_default='0.0'),
        sa.Column('toxicity_rate', sa.Float(), server_default='0.0'),
        sa.Column('report_rate', sa.Float(), server_default='0.0'),
        sa.Column('mod_action_rate', sa.Float(), server_default='0.0'),
        sa.Column('current_slowmode', sa.Integer(), server_default='0'),
        sa.Column('auto_slowmode_active', sa.Boolean(), server_default='false'),
        sa.Column('last_calculated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('guild_id', 'channel_id', name='uq_channel_heat'),
    )
    op.create_index('idx_heat_channel', 'channel_heat', ['guild_id', 'channel_id'])
    op.create_index('idx_heat_score', 'channel_heat', ['heat_score'])

    # 11. Events Ingested (Idempotency)
    op.create_table(
        'events_ingested',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('event_id', sa.String(64), unique=True, nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('user_id', sa.BigInteger()),
        sa.Column('channel_id', sa.BigInteger()),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('processing_time_ms', sa.Integer()),
        sa.Column('shard_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_events_event_id', 'events_ingested', ['event_id'])
    op.create_index('idx_events_guild', 'events_ingested', ['guild_id', 'created_at'])

    # 12. Discord Actions
    op.create_table(
        'discord_actions',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('target_user_id', sa.BigInteger()),
        sa.Column('target_channel_id', sa.BigInteger()),
        sa.Column('target_message_id', sa.BigInteger()),
        sa.Column('triggered_by', sa.BigInteger()),
        sa.Column('case_id', sa.BigInteger(), sa.ForeignKey('mod_cases.id')),
        sa.Column('executed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('success', sa.Boolean(), server_default='true'),
        sa.Column('error_message', sa.Text()),
        sa.Column('discord_audit_id', sa.BigInteger()),
        sa.Column('action_id', sa.String(64), unique=True, nullable=False),
    )
    op.create_index('idx_actions_guild', 'discord_actions', ['guild_id', 'executed_at'])
    op.create_index('idx_actions_user', 'discord_actions', ['target_user_id'])
    op.create_index('idx_actions_case', 'discord_actions', ['case_id'])

    # 13. Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('actor_id', sa.BigInteger(), nullable=False),
        sa.Column('actor_type', sa.String(20)),
        sa.Column('target_type', sa.String(20)),
        sa.Column('target_id', sa.BigInteger()),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('details', JSONB()),
        sa.Column('case_id', sa.BigInteger()),
        sa.Column('ticket_id', sa.BigInteger()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_audit_guild', 'audit_events', ['guild_id', 'created_at'])
    op.create_index('idx_audit_actor', 'audit_events', ['actor_id'])
    op.create_index('idx_audit_type', 'audit_events', ['event_type'])

    # 14. Giveaways
    op.create_table(
        'giveaways',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('host_id', sa.BigInteger()),
        sa.Column('prize', sa.String(255)),
        sa.Column('winner_count', sa.Integer(), server_default='1'),
        sa.Column('ends_at', sa.DateTime()),
        sa.Column('ended', sa.Boolean(), server_default='false'),
        sa.Column('winners', JSONB(), server_default='[]'),
        sa.Column('required_role_id', sa.BigInteger()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 15. Birthdays
    op.create_table(
        'birthdays',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_birthdays_user', 'birthdays', ['guild_id', 'user_id'])

    # 16. Temp Mutes
    op.create_table(
        'temp_mutes',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('moderator_id', sa.BigInteger()),
        sa.Column('reason', sa.Text()),
        sa.Column('muted_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('unmute_at', sa.DateTime()),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 17. Jailed Users
    op.create_table(
        'jailed_users',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('jailed_by', sa.BigInteger()),
        sa.Column('reason', sa.Text()),
        sa.Column('previous_roles', JSONB(), server_default='[]'),
        sa.Column('jailed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('release_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('jailed_users')
    op.drop_table('temp_mutes')
    op.drop_table('birthdays')
    op.drop_table('giveaways')
    op.drop_table('audit_events')
    op.drop_table('discord_actions')
    op.drop_table('events_ingested')
    op.drop_table('channel_heat')
    op.drop_table('ticket_tags')
    op.drop_table('ticket_messages_v2')
    op.drop_table('tickets_v2')
    op.drop_table('evidence')
    op.drop_table('mod_cases')
    op.drop_table('user_risk_profiles')
    op.drop_table('policy_versions')
    op.drop_table('policies')
    op.drop_table('governance_configs')
