"""user notification settings

Adds user.notification_settings: per notification type and channel
({"lab_membership_request": {"email": true, "browser": false}, ...}).
Missing entries use the defaults in app.core.notification_catalog.

Revision ID: f1b3d5e7a9c0
Revises: e8a0c2d4f6b8
Create Date: 2026-11-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1b3d5e7a9c0'
down_revision: Union[str, None] = 'e8a0c2d4f6b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column(
            'notification_settings',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('user', 'notification_settings')
