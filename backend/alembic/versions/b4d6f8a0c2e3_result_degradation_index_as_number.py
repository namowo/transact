"""result degradation index as a decimal number

Replaces the degradation category lookup on result with a free decimal
degradation index and drops the now unused degradation_category table.
Existing category selections (severe, moderate, ...) have no numeric
equivalent and are dropped.

Revision ID: b4d6f8a0c2e3
Revises: a3c5e7f9b1d2
Create Date: 2026-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b4d6f8a0c2e3'
down_revision: Union[str, None] = 'a3c5e7f9b1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('result', sa.Column('degradation_index', sa.Float(), nullable=True))
    op.drop_constraint('result_degradation_category_id_fkey', 'result', type_='foreignkey')
    op.drop_column('result', 'degradation_category_id')
    op.drop_index(op.f('ix_degradation_category_id'), table_name='degradation_category')
    op.drop_table('degradation_category')


def downgrade() -> None:
    op.create_table(
        'degradation_category',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_degradation_category_id'), 'degradation_category', ['id'], unique=False)
    op.add_column(
        'result',
        sa.Column('degradation_category_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'result_degradation_category_id_fkey',
        'result',
        'degradation_category',
        ['degradation_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('result', 'degradation_index')
