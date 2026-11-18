"""add data model

Revision ID: c2d3e4f5a6b8
Revises: b1c2d3e4f5a7
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b8'
down_revision: Union[str, None] = 'b1c2d3e4f5a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'data_model',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_data_model_id'), 'data_model', ['id'], unique=False)
    op.create_index(op.f('ix_data_model_owner_id'), 'data_model', ['owner_id'], unique=False)
    op.create_index(op.f('ix_data_model_is_public'), 'data_model', ['is_public'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_data_model_is_public'), table_name='data_model')
    op.drop_index(op.f('ix_data_model_owner_id'), table_name='data_model')
    op.drop_index(op.f('ix_data_model_id'), table_name='data_model')
    op.drop_table('data_model')
