"""add scenario name, individual_scenario and item_scenario

Revision ID: c9d8e7f6a5b4
Revises: 4d5e6f7a8b9c
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c9d8e7f6a5b4'
down_revision: Union[str, None] = '4d5e6f7a8b9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scenario', sa.Column('name', sa.String(), nullable=True))
    # Existing scenarios were unnamed: number them in a stable order.
    op.execute(
        """
        UPDATE scenario SET name = numbered.label
        FROM (
            SELECT id, 'Scenario ' || ROW_NUMBER() OVER (ORDER BY id) AS label
            FROM scenario
        ) AS numbered
        WHERE scenario.id = numbered.id
        """
    )
    op.alter_column('scenario', 'name', nullable=False)

    op.create_table(
        'individual_scenario',
        sa.Column('individual_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('individual.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenario.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table(
        'item_scenario',
        sa.Column('item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('item.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenario.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('item_scenario')
    op.drop_table('individual_scenario')
    op.drop_column('scenario', 'name')
