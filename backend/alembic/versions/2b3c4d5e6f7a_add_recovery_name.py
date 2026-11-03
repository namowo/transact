"""add recovery name

Revision ID: 2b3c4d5e6f7a
Revises: 1cafb711a5b7
Create Date: 2026-10-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b3c4d5e6f7a'
down_revision: Union[str, None] = '1cafb711a5b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recovery', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('recovery', 'name')
