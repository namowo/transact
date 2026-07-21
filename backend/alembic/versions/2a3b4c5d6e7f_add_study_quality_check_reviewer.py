"""add study quality check reviewer

Revision ID: 2a3b4c5d6e7f
Revises: 1f2a3b4c5d6e
Create Date: 2026-07-21 15:34:53.110313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a3b4c5d6e7f'
down_revision: Union[str, None] = '1f2a3b4c5d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('study', sa.Column('quality_checked_by_id', sa.Integer(), nullable=True))
    op.add_column('study', sa.Column('quality_checked_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'fk_study_quality_checked_by_id_user',
        'study', 'user', ['quality_checked_by_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_study_quality_checked_by_id_user', 'study', type_='foreignkey')
    op.drop_column('study', 'quality_checked_at')
    op.drop_column('study', 'quality_checked_by_id')
