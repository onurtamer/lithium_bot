"""add_guild_module_settings_and_panel_audit_logs

Revision ID: web_control_center_001
Revises: bot_autocracy_001
Create Date: 2026-01-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'web_control_center_001'
down_revision: Union[str, None] = 'bot_autocracy_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # Guild Module Settings Table
    # Stores module configurations per guild
    # ========================================
    op.create_table(
        'guild_module_settings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('module_key', sa.String(50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('config_json', JSONB, nullable=True),
        sa.Column('draft_json', JSONB, nullable=True),  # Unpublished changes
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_by', sa.String(20), nullable=True),  # Discord user ID
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Composite unique constraint
    op.create_unique_constraint(
        'uq_guild_module', 
        'guild_module_settings', 
        ['guild_id', 'module_key']
    )
    
    # Index for guild lookups
    op.create_index(
        'ix_guild_module_settings_guild_id',
        'guild_module_settings',
        ['guild_id']
    )

    # ========================================
    # Config Versions Table
    # Stores historical versions for rollback
    # ========================================
    op.create_table(
        'config_versions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('module_key', sa.String(50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('config_json', JSONB, nullable=False),
        sa.Column('created_by', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('note', sa.String(255), nullable=True),  # Optional description
        sa.PrimaryKeyConstraint('id')
    )
    
    # Index for version history lookups
    op.create_index(
        'ix_config_versions_lookup',
        'config_versions',
        ['guild_id', 'module_key', 'version']
    )

    # ========================================
    # Panel Audit Logs Table
    # Tracks changes made via the web panel
    # ========================================
    op.create_table(
        'panel_audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(20), nullable=False),  # Discord user ID
        sa.Column('action', sa.String(50), nullable=False),  # create, update, delete, enable, disable
        sa.Column('module_key', sa.String(50), nullable=True),
        sa.Column('target_type', sa.String(50), nullable=True),  # module, role, channel, etc.
        sa.Column('target_id', sa.String(50), nullable=True),
        sa.Column('changes', JSONB, nullable=True),  # Diff of changes
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Index for guild audit log queries
    op.create_index(
        'ix_panel_audit_logs_guild_id',
        'panel_audit_logs',
        ['guild_id', 'created_at']
    )
    
    # Index for user activity tracking
    op.create_index(
        'ix_panel_audit_logs_user_id',
        'panel_audit_logs',
        ['user_id', 'created_at']
    )

    # ========================================
    # Bot Audit Events Table
    # Tracks bot actions for the dashboard
    # ========================================
    op.create_table(
        'bot_audit_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),  # automod_trigger, jail, mute, etc.
        sa.Column('module_key', sa.String(50), nullable=True),
        sa.Column('actor_id', sa.String(20), nullable=True),  # Bot or moderator user ID
        sa.Column('target_id', sa.String(20), nullable=True),  # Affected user ID
        sa.Column('target_type', sa.String(20), nullable=True),  # user, message, channel
        sa.Column('metadata', JSONB, nullable=True),  # Event-specific data
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Index for event timeline queries
    op.create_index(
        'ix_bot_audit_events_guild_timeline',
        'bot_audit_events',
        ['guild_id', 'created_at']
    )
    
    # Index for module-specific event queries
    op.create_index(
        'ix_bot_audit_events_module',
        'bot_audit_events',
        ['guild_id', 'module_key', 'created_at']
    )

    # ========================================
    # Guild Memberships Table
    # Panel RBAC - who can access which guilds
    # ========================================
    op.create_table(
        'guild_memberships',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(20), nullable=False),  # Discord user ID
        sa.Column('role', sa.String(20), nullable=False, server_default='viewer'),  # admin, moderator, viewer
        sa.Column('permissions', JSONB, nullable=True),  # Fine-grained permissions
        sa.Column('granted_by', sa.String(20), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Composite unique constraint
    op.create_unique_constraint(
        'uq_guild_membership',
        'guild_memberships',
        ['guild_id', 'user_id']
    )
    
    # Index for user's guilds lookup
    op.create_index(
        'ix_guild_memberships_user_id',
        'guild_memberships',
        ['user_id']
    )


def downgrade() -> None:
    op.drop_table('guild_memberships')
    op.drop_table('bot_audit_events')
    op.drop_table('panel_audit_logs')
    op.drop_table('config_versions')
    op.drop_table('guild_module_settings')
