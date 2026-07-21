"""add user permission flags

Revision ID: bc7f31965aba
Revises: cc4448bf52aa
Create Date: 2026-07-21 15:32:53.110313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc7f31965aba'
down_revision: Union[str, None] = 'cc4448bf52aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('can_quality_check', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user', sa.Column('can_manage_lab_users', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('user', 'can_manage_lab_users')
    op.drop_column('user', 'can_quality_check')
