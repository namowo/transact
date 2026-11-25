"""add planning checklist

Revision ID: 339199bba40e
Revises: d3e4f5a6b7c9
Create Date: 2026-11-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '339199bba40e'
down_revision: Union[str, None] = 'd3e4f5a6b7c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'planning_checklist',
        sa.Column(
            'laboratory_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('laboratory.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column('sections', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table('planning_checklist')
