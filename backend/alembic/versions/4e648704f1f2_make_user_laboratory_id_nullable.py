"""make user laboratory_id nullable

Revision ID: 4e648704f1f2
Revises: 1677e212d8a2
Create Date: 2026-07-17 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e648704f1f2'
down_revision: Union[str, None] = '1677e212d8a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('user', 'laboratory_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('user', 'laboratory_id',
               existing_type=sa.INTEGER(),
               nullable=False)
