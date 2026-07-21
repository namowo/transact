"""add laboratory approval status

Revision ID: 1f2a3b4c5d6e
Revises: bc7f31965aba
Create Date: 2026-07-21 15:33:53.110313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f2a3b4c5d6e'
down_revision: Union[str, None] = 'bc7f31965aba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'laboratory',
        sa.Column(
            'approval_status',
            sa.Enum(
                'pending', 'approved', 'denied',
                name='laboratory_approval_status',
                native_enum=False,
                length=20,
            ),
            server_default=sa.text("'approved'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('laboratory', 'approval_status')
