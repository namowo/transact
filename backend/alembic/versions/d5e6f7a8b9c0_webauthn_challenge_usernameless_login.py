"""webauthn challenge usernameless login

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-09-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('webauthn_challenge', 'user_id', nullable=True)
    op.create_unique_constraint(
        'uq_webauthn_challenge_challenge', 'webauthn_challenge', ['challenge']
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_webauthn_challenge_challenge', 'webauthn_challenge', type_='unique'
    )
    op.alter_column('webauthn_challenge', 'user_id', nullable=False)
