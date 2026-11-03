"""add contact chains

Revision ID: b3c4d5e6f7a8
Revises: e2f3a4b5c6d7
Create Date: 2026-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'contact_template',
        sa.Column('previous_contact_template_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_contact_template_previous_contact_template_id',
        'contact_template', 'contact_template',
        ['previous_contact_template_id'], ['id'], ondelete='SET NULL',
    )
    op.add_column(
        'contact',
        sa.Column('previous_contact_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_contact_previous_contact_id',
        'contact', 'contact',
        ['previous_contact_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_contact_previous_contact_id', 'contact', type_='foreignkey')
    op.drop_column('contact', 'previous_contact_id')
    op.drop_constraint(
        'fk_contact_template_previous_contact_template_id', 'contact_template', type_='foreignkey'
    )
    op.drop_column('contact_template', 'previous_contact_template_id')
