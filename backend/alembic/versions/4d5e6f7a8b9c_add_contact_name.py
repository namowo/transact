"""add contact name

Revision ID: 4d5e6f7a8b9c
Revises: a7b8c9d0e1f2
Create Date: 2026-10-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d5e6f7a8b9c'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contact', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('contact', 'name')
