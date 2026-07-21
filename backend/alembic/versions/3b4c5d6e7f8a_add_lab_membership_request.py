"""add lab membership request

Revision ID: 3b4c5d6e7f8a
Revises: 2a3b4c5d6e7f
Create Date: 2026-07-21 15:35:53.110313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b4c5d6e7f8a'
down_revision: Union[str, None] = '2a3b4c5d6e7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lab_membership_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('laboratory_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'pending', 'approved', 'denied',
                name='lab_membership_request_status',
                native_enum=False,
                length=20,
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['laboratory_id'], ['laboratory.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_lab_membership_request_id'), 'lab_membership_request', ['id'], unique=False
    )
    op.create_index(
        'ix_lab_membership_request_one_pending_per_user',
        'lab_membership_request',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        'ix_lab_membership_request_one_pending_per_user',
        table_name='lab_membership_request',
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index(op.f('ix_lab_membership_request_id'), table_name='lab_membership_request')
    op.drop_table('lab_membership_request')
