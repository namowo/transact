"""epg analysis dye channel thresholds, pcr kit ref, stutter filter dropdown; epg interpretation modelled parameters m2m, description fields

Revision ID: bd6cc82be73f
Revises: 7f9e3630c42d
Create Date: 2026-10-26 18:57:37.392995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd6cc82be73f'
down_revision: Union[str, None] = '7f9e3630c42d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('dye_channel',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dye_channel_id'), 'dye_channel', ['id'], unique=False)
    op.create_table('modelled_parameter',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modelled_parameter_id'), 'modelled_parameter', ['id'], unique=False)
    op.create_table('epg_analysis_method_dye_channel_threshold',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('epg_analysis_method_id', sa.UUID(), nullable=False),
    sa.Column('dye_channel_id', sa.UUID(), nullable=True),
    sa.Column('analytical_threshold', sa.Double(), nullable=True),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dye_channel_id'], ['dye_channel.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['epg_analysis_method_id'], ['epg_analysis_method.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_epg_analysis_method_dye_channel_threshold_id'), 'epg_analysis_method_dye_channel_threshold', ['id'], unique=False)
    op.create_table('epg_interpretation_method_modelled_parameter',
    sa.Column('epg_interpretation_method_id', sa.UUID(), nullable=False),
    sa.Column('modelled_parameter_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['epg_interpretation_method_id'], ['epg_interpretation_method.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['modelled_parameter_id'], ['modelled_parameter.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('epg_interpretation_method_id', 'modelled_parameter_id')
    )
    op.add_column('epg_analysis_method', sa.Column('pcr_kit_id', sa.UUID(), nullable=True))
    op.add_column('epg_analysis_method', sa.Column('stutter_filter_id', sa.UUID(), nullable=True))
    op.add_column('epg_analysis_method', sa.Column('description', sa.String(), nullable=True))
    op.create_foreign_key('fk_epg_analysis_method_pcr_kit_id', 'epg_analysis_method', 'pcr_kit', ['pcr_kit_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_epg_analysis_method_stutter_filter_id', 'epg_analysis_method', 'stutter_filter', ['stutter_filter_id'], ['id'], ondelete='SET NULL')
    op.drop_column('epg_analysis_method', 'analytical_threshold')
    op.drop_column('epg_analysis_method', 'stutter_filter')
    op.add_column('epg_interpretation_method', sa.Column('description', sa.String(), nullable=True))
    op.drop_column('epg_interpretation_method', 'parameters_modelled_by_software')


def downgrade() -> None:
    op.add_column('epg_interpretation_method', sa.Column('parameters_modelled_by_software', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('epg_interpretation_method', 'description')
    op.add_column('epg_analysis_method', sa.Column('stutter_filter', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('epg_analysis_method', sa.Column('analytical_threshold', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint('fk_epg_analysis_method_pcr_kit_id', 'epg_analysis_method', type_='foreignkey')
    op.drop_constraint('fk_epg_analysis_method_stutter_filter_id', 'epg_analysis_method', type_='foreignkey')
    op.drop_column('epg_analysis_method', 'description')
    op.drop_column('epg_analysis_method', 'stutter_filter_id')
    op.drop_column('epg_analysis_method', 'pcr_kit_id')
    op.drop_table('epg_interpretation_method_modelled_parameter')
    op.drop_index(op.f('ix_epg_analysis_method_dye_channel_threshold_id'), table_name='epg_analysis_method_dye_channel_threshold')
    op.drop_table('epg_analysis_method_dye_channel_threshold')
    op.drop_index(op.f('ix_modelled_parameter_id'), table_name='modelled_parameter')
    op.drop_table('modelled_parameter')
    op.drop_index(op.f('ix_dye_channel_id'), table_name='dye_channel')
    op.drop_table('dye_channel')
