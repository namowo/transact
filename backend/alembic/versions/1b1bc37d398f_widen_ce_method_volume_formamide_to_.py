"""widen ce_method volume_formamide to float

Revision ID: 1b1bc37d398f
Revises: d85ee6625e66
Create Date: 2026-10-26 18:38:47.518086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b1bc37d398f'
down_revision: Union[str, None] = 'd85ee6625e66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('ce_method', 'volume_formamide',
               existing_type=sa.INTEGER(),
               type_=sa.Double(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('ce_method', 'volume_formamide',
               existing_type=sa.Double(),
               type_=sa.INTEGER(),
               existing_nullable=True)
