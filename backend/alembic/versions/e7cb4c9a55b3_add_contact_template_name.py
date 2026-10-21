"""add contact template name

Revision ID: e7cb4c9a55b3
Revises: dd781ae85686
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7cb4c9a55b3'
down_revision: Union[str, None] = 'dd781ae85686'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contact_template', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('contact_template', 'name')
