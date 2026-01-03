"""production_upgrade_001 - Add message metrics and guild settings tables

Revision ID: production_upgrade_001
Revises: web_control_center_001
Create Date: 2026-01-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'production_upgrade_001'
down_revision: Union[str, None] = 'web_control_center_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # Message Metrics Daily Table
    # Stores daily message counts per guild
    # ========================================
    op.create_table(
        'message_metrics_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Unique constraint for guild + date
    op.create_unique_constraint(
        'uq_message_metrics_guild_date',
        'message_metrics_daily',
        ['guild_id', 'date']
    )
    
    # Index for efficient queries
    op.create_index(
        'ix_message_metrics_guild_date',
        'message_metrics_daily',
        ['guild_id', 'date']
    )

    # ========================================
    # Guild Settings Table
    # Centralized settings storage
    # ========================================
    op.create_table(
        'guild_settings',
        sa.Column('guild_id', sa.String(20), nullable=False),
        sa.Column('prefix', sa.String(10), nullable=False, server_default='!'),
        sa.Column('language', sa.String(5), nullable=False, server_default='tr'),
        sa.Column('log_channel_id', sa.String(20), nullable=True),
        sa.Column('welcome_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('welcome_channel_id', sa.String(20), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('dm_on_warn', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('dm_on_mute', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_join', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_leave', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_ban', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings_json', JSONB, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint('guild_id')
    )


def downgrade() -> None:
    op.drop_table('guild_settings')
    op.drop_table('message_metrics_daily')
