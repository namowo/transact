"""user sign-in lockout

Counts wrong passwords in a row; too many lock the account until an admin
unlocks it.

Revision ID: b3d5f7a9c1e2
Revises: a2c4e6f8b0d1
Create Date: 2026-11-26 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d5f7a9c1e2'
down_revision: Union[str, None] = 'a2c4e6f8b0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column(
            'failed_login_attempts',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
    )
    op.add_column('user', sa.Column('locked_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'locked_at')
    op.drop_column('user', 'failed_login_attempts')
