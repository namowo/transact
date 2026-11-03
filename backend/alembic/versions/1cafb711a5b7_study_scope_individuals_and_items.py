"""study-scope individuals and items

Revision ID: 1cafb711a5b7
Revises: b1c2d3e4f5a6
Create Date: 2026-10-26 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1cafb711a5b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'individual',
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'individual_study_id_fkey',
        'individual',
        'study',
        ['study_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.create_table(
        'study_item',
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['item.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('study_id', 'item_id'),
    )


def downgrade() -> None:
    op.drop_table('study_item')

    op.drop_constraint('individual_study_id_fkey', 'individual', type_='foreignkey')
    op.drop_column('individual', 'study_id')
