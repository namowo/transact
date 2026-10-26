"""swab method wetting agent type

Revision ID: aa541a687a29
Revises: bd6cc82be73f
Create Date: 2026-10-26 19:17:24.302568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa541a687a29'
down_revision: Union[str, None] = 'bd6cc82be73f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('swab_method', sa.Column('volume_of_wetting_agent_type', sa.String(), nullable=True))
    op.drop_column('swab_method', 'specification')


def downgrade() -> None:
    op.add_column('swab_method', sa.Column('specification', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('swab_method', 'volume_of_wetting_agent_type')
