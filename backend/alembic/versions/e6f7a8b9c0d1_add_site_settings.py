"""add site settings

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'site_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_print_mode', sa.String(), server_default='text', nullable=False),
        sa.Column('site_print_text', sa.String(), nullable=True),
        sa.Column('site_print_url', sa.String(), nullable=True),
        sa.Column('privacy_policy_mode', sa.String(), server_default='text', nullable=False),
        sa.Column('privacy_policy_text', sa.String(), nullable=True),
        sa.Column('privacy_policy_url', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_site_settings_id'), 'site_settings', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_site_settings_id'), table_name='site_settings')
    op.drop_table('site_settings')
