"""add scenario owning_study_id

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scenario', sa.Column('owning_study_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'scenario_owning_study_id_fkey',
        'scenario',
        'study',
        ['owning_study_id'],
        ['id'],
        ondelete='SET NULL',
    )
    # Backfill existing scenarios with one of their currently linked studies,
    # so they remain editable by that study instead of becoming read-only
    # everywhere.
    op.execute(
        """
        UPDATE scenario
        SET owning_study_id = sub.study_id
        FROM (
            SELECT DISTINCT ON (scenario_id) scenario_id, study_id
            FROM study_scenario
            ORDER BY scenario_id, study_id
        ) AS sub
        WHERE scenario.id = sub.scenario_id
        """
    )


def downgrade() -> None:
    op.drop_constraint('scenario_owning_study_id_fkey', 'scenario', type_='foreignkey')
    op.drop_column('scenario', 'owning_study_id')
