"""user invitations

Adds user.invitation_pending: set while an invited user hasn't accepted
their invitation (and chosen a password) yet.

Revision ID: e8a0c2d4f6b8
Revises: d7f9b1c3e5a7
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8a0c2d4f6b8'
down_revision: Union[str, None] = 'd7f9b1c3e5a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column(
            'invitation_pending',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )


def downgrade() -> None:
    op.drop_column('user', 'invitation_pending')
