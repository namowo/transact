"""move scenario-contact FK from scenario to contact

Revision ID: a1b2c3d4e5f6
Revises: 9f1a2b3c4d5e
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9f1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contact', sa.Column('scenario_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE contact
        SET scenario_id = scenario.id
        FROM scenario
        WHERE scenario.contact_id = contact.id
        """
    )
    op.alter_column('contact', 'scenario_id', nullable=False)
    op.create_foreign_key(
        'contact_scenario_id_fkey',
        'contact',
        'scenario',
        ['scenario_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_constraint('scenario_contact_id_fkey', 'scenario', type_='foreignkey')
    op.drop_column('scenario', 'contact_id')


def downgrade() -> None:
    op.add_column('scenario', sa.Column('contact_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE scenario
        SET contact_id = contact.id
        FROM contact
        WHERE contact.scenario_id = scenario.id
        """
    )
    op.create_foreign_key(
        'scenario_contact_id_fkey',
        'scenario',
        'contact',
        ['contact_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_constraint('contact_scenario_id_fkey', 'contact', type_='foreignkey')
    op.drop_column('contact', 'scenario_id')
