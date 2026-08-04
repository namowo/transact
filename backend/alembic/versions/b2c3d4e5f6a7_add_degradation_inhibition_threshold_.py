"""degradation/inhibition/threshold/stutter-filter lookup tables

Revision ID: b2c3d4e5f6a7
Revises: 005b0c0560e8
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '005b0c0560e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NAME_ONLY_TABLES = [
    'degradation_category',
    'inhibition_category',
    'application_analytical_threshold',
    'stutter_filter',
]


def upgrade() -> None:
    for table_name in NAME_ONLY_TABLES:
        op.create_table(
            table_name,
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f(f'ix_{table_name}_id'), table_name, ['id'], unique=True)

    # result: degradation (str), inhibition (bool) -> FK lookups
    op.add_column('result', sa.Column('degradation_category_id', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('inhibition_category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'result_degradation_category_id_fkey',
        'result',
        'degradation_category',
        ['degradation_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'result_inhibition_category_id_fkey',
        'result',
        'inhibition_category',
        ['inhibition_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('result', 'degradation')
    op.drop_column('result', 'inhibition')

    # epg_interpretation_method: new application_analytical_threshold_id, stutter_filter_id FKs
    op.add_column(
        'epg_interpretation_method',
        sa.Column('application_analytical_threshold_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'epg_interpretation_method', sa.Column('stutter_filter_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'epg_interpretation_method_app_analytical_threshold_id_fkey',
        'epg_interpretation_method',
        'application_analytical_threshold',
        ['application_analytical_threshold_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'epg_interpretation_method_stutter_filter_id_fkey',
        'epg_interpretation_method',
        'stutter_filter',
        ['stutter_filter_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'epg_interpretation_method_stutter_filter_id_fkey',
        'epg_interpretation_method',
        type_='foreignkey',
    )
    op.drop_constraint(
        'epg_interpretation_method_app_analytical_threshold_id_fkey',
        'epg_interpretation_method',
        type_='foreignkey',
    )
    op.drop_column('epg_interpretation_method', 'stutter_filter_id')
    op.drop_column('epg_interpretation_method', 'application_analytical_threshold_id')

    op.add_column('result', sa.Column('inhibition', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('result', sa.Column('degradation', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('result_inhibition_category_id_fkey', 'result', type_='foreignkey')
    op.drop_constraint('result_degradation_category_id_fkey', 'result', type_='foreignkey')
    op.drop_column('result', 'inhibition_category_id')
    op.drop_column('result', 'degradation_category_id')

    for table_name in reversed(NAME_ONLY_TABLES):
        op.drop_index(op.f(f'ix_{table_name}_id'), table_name=table_name)
        op.drop_table(table_name)
