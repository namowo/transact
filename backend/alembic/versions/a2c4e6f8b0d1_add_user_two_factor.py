"""user two-factor authentication

Adds the authenticator app (TOTP) secret, its recovery codes, replay and
brute-force protection to the user.

Revision ID: a2c4e6f8b0d1
Revises: f1b3d5e7a9c0
Create Date: 2026-11-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a2c4e6f8b0d1'
down_revision: Union[str, None] = 'f1b3d5e7a9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('totp_secret', sa.String(), nullable=True))
    op.add_column('user', sa.Column('totp_pending_secret', sa.String(), nullable=True))
    op.add_column('user', sa.Column('totp_last_used_step', sa.BigInteger(), nullable=True))
    op.add_column(
        'user',
        sa.Column(
            'totp_recovery_codes',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        'user',
        sa.Column(
            'totp_failed_attempts',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
    )
    op.add_column('user', sa.Column('totp_locked_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'totp_locked_until')
    op.drop_column('user', 'totp_failed_attempts')
    op.drop_column('user', 'totp_recovery_codes')
    op.drop_column('user', 'totp_last_used_step')
    op.drop_column('user', 'totp_pending_secret')
    op.drop_column('user', 'totp_secret')
