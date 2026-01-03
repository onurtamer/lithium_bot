"""add_access_keys_table

Revision ID: 5f2a8c1b9d3e
Revises: 7bd60a5ba720
Create Date: 2026-01-03 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f2a8c1b9d3e'
down_revision: Union[str, None] = '4e1d9b3a5c2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create access_keys table for key-based authentication"""
    op.create_table(
        'access_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=30), nullable=False),
        sa.Column('guild_discord_id', sa.String(), nullable=False),
        sa.Column('created_by_discord_id', sa.String(), nullable=False),
        sa.Column('expires_at', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_access_keys_key', 'access_keys', ['key'], unique=True)
    op.create_index('ix_access_keys_guild_discord_id', 'access_keys', ['guild_discord_id'], unique=False)


def downgrade() -> None:
    """Drop access_keys table"""
    op.drop_index('ix_access_keys_guild_discord_id', table_name='access_keys')
    op.drop_index('ix_access_keys_key', table_name='access_keys')
    op.drop_table('access_keys')
