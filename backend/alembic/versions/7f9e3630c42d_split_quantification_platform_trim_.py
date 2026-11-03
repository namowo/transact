"""split quantification platform, trim manufacturer fields, add deviations field

Revision ID: 7f9e3630c42d
Revises: 1b1bc37d398f
Create Date: 2026-10-26 18:45:11.963332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9e3630c42d'
down_revision: Union[str, None] = '1b1bc37d398f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('quantification_platform',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quantification_platform_id'), 'quantification_platform', ['id'], unique=False)
    op.add_column('extraction_method', sa.Column('abbreviations_to_manufacturers_protocol', sa.String(), nullable=True))
    op.add_column('pcr_method', sa.Column('abbreviations_to_manufacturers_protocol', sa.String(), nullable=True))
    op.drop_constraint(op.f('quantification_method_platform_id_fkey'), 'quantification_method', type_='foreignkey')
    op.drop_constraint(op.f('quantification_method_manufacturer_id_fkey'), 'quantification_method', type_='foreignkey')
    op.create_foreign_key('fk_quantification_method_platform_id', 'quantification_method', 'quantification_platform', ['platform_id'], ['id'], ondelete='SET NULL')
    op.drop_column('quantification_method', 'manufacturer_id')
    op.drop_column('quantification_method', 'description_of_protocol')


def downgrade() -> None:
    op.add_column('quantification_method', sa.Column('description_of_protocol', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('quantification_method', sa.Column('manufacturer_id', sa.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint('fk_quantification_method_platform_id', 'quantification_method', type_='foreignkey')
    op.create_foreign_key(op.f('quantification_method_manufacturer_id_fkey'), 'quantification_method', 'manufacturer', ['manufacturer_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('quantification_method_platform_id_fkey'), 'quantification_method', 'platform', ['platform_id'], ['id'], ondelete='SET NULL')
    op.drop_column('pcr_method', 'abbreviations_to_manufacturers_protocol')
    op.drop_column('extraction_method', 'abbreviations_to_manufacturers_protocol')
    op.drop_index(op.f('ix_quantification_platform_id'), table_name='quantification_platform')
    op.drop_table('quantification_platform')
