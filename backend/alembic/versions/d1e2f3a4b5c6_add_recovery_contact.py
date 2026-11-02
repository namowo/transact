"""add recovery contact

Revision ID: d1e2f3a4b5c6
Revises: c9d8e7f6a5b4
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c9d8e7f6a5b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'recovery',
        sa.Column(
            'contact_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('contact.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    # Existing recoveries: link the contact when the surface belongs to exactly one.
    op.execute(
        """
        UPDATE recovery SET contact_id = single.contact_id
        FROM (
            SELECT surface_id, MIN(contact_id::text)::uuid AS contact_id
            FROM (
                SELECT donor_surface_id AS surface_id, id AS contact_id FROM contact
                UNION ALL
                SELECT recipient_surface_id, id FROM contact
            ) AS links
            WHERE surface_id IS NOT NULL
            GROUP BY surface_id
            HAVING COUNT(*) = 1
        ) AS single
        WHERE recovery.surface_id = single.surface_id
        """
    )


def downgrade() -> None:
    op.drop_column('recovery', 'contact_id')
