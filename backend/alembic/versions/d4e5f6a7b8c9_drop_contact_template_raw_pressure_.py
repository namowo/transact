"""drop contact_template raw pressure/friction_applied columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('contact_template', 'pressure')
    op.drop_column('contact_template', 'friction_applied')


def downgrade() -> None:
    op.add_column('contact_template', sa.Column('friction_applied', sa.Float(), nullable=True))
    op.add_column('contact_template', sa.Column('pressure', sa.Float(), nullable=True))
