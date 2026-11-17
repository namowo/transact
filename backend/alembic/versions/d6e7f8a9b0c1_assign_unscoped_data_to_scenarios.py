"""assign individuals and items without scenarios to all study scenarios

Individuals and items used to mean "all scenarios" when they had no
scenario links. They now must belong to at least one scenario explicitly,
so existing unlinked ones are linked to every scenario of their study.
Items are a shared catalog, so this is checked per study the item is in.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-11-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, None] = 'c5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO individual_scenario (individual_id, scenario_id)
        SELECT i.id, ss.scenario_id
        FROM individual i
        JOIN study_scenario ss ON ss.study_id = i.study_id
        WHERE NOT EXISTS (
            SELECT 1 FROM individual_scenario isc WHERE isc.individual_id = i.id
        )
        """
    )
    op.execute(
        """
        INSERT INTO item_scenario (item_id, scenario_id)
        SELECT si.item_id, ss.scenario_id
        FROM study_item si
        JOIN study_scenario ss ON ss.study_id = si.study_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM item_scenario isc
            JOIN study_scenario own ON own.scenario_id = isc.scenario_id
            WHERE isc.item_id = si.item_id AND own.study_id = si.study_id
        )
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    # The previous "no scenario = all scenarios" state cannot be told apart
    # from explicit links, so links are kept.
    pass
