"""add study checklist progress

Revision ID: fcf2d249fcdc
Revises: 339199bba40e
Create Date: 2026-11-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fcf2d249fcdc'
down_revision: Union[str, None] = '339199bba40e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'study_checklist_progress',
        sa.Column(
            'study_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('study.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column(
            'checked',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'notes',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table('study_checklist_progress')
