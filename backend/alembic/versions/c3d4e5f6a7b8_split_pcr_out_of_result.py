"""split pcr out of result

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pcr',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.Integer(), nullable=False),
        sa.Column('dna_quantity', sa.Float(), nullable=True),
        sa.Column('pcr_method_id', sa.Integer(), nullable=True),
        sa.Column('sample_input_volume_in_pcr', sa.Float(), nullable=True),
        sa.Column('dna_input_amount_in_pcr', sa.Float(), nullable=True),
        sa.Column('post_pcr_treatment_method_id', sa.Integer(), nullable=True),
        sa.Column('ce_method_id', sa.Integer(), nullable=True),
        sa.Column('epg_analysis_method_id', sa.Integer(), nullable=True),
        sa.Column('epg_interpretation_method_id', sa.Integer(), nullable=True),
        sa.Column('no_of_contributors', sa.Integer(), nullable=True),
        sa.Column('mixture_proportion', sa.Float(), nullable=True),
        sa.Column('total_rfu', sa.Integer(), nullable=True),
        sa.Column('total_no_of_alleles', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['result_id'], ['result.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pcr_method_id'], ['pcr_method.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(
            ['post_pcr_treatment_method_id'], ['post_pcr_treatment_method.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(['ce_method_id'], ['ce_method.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(
            ['epg_analysis_method_id'], ['epg_analysis_method.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['epg_interpretation_method_id'], ['epg_interpretation_method.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pcr_id'), 'pcr', ['id'], unique=True)

    op.execute(
        """
        INSERT INTO pcr (
            result_id, dna_quantity, pcr_method_id, sample_input_volume_in_pcr,
            dna_input_amount_in_pcr, post_pcr_treatment_method_id, ce_method_id,
            epg_analysis_method_id, epg_interpretation_method_id, no_of_contributors,
            mixture_proportion, total_rfu, total_no_of_alleles
        )
        SELECT
            id, dna_quantity, pcr_method_id, sample_input_volume_in_pcr,
            dna_input_amount_in_pcr, post_pcr_treatment_method_id, ce_method_id,
            epg_analysis_method_id, epg_interpretation_method_id, no_of_contributors,
            mixture_proportion, total_rfu, total_no_of_alleles
        FROM result
        WHERE dna_quantity IS NOT NULL
           OR pcr_method_id IS NOT NULL
           OR sample_input_volume_in_pcr IS NOT NULL
           OR dna_input_amount_in_pcr IS NOT NULL
           OR post_pcr_treatment_method_id IS NOT NULL
           OR ce_method_id IS NOT NULL
           OR epg_analysis_method_id IS NOT NULL
           OR epg_interpretation_method_id IS NOT NULL
           OR no_of_contributors IS NOT NULL
           OR mixture_proportion IS NOT NULL
           OR total_rfu IS NOT NULL
           OR total_no_of_alleles IS NOT NULL
        """
    )

    op.drop_constraint('result_pcr_method_id_fkey', 'result', type_='foreignkey')
    op.drop_constraint('result_post_pcr_treatment_method_id_fkey', 'result', type_='foreignkey')
    op.drop_constraint('result_ce_method_id_fkey', 'result', type_='foreignkey')
    op.drop_constraint('result_epg_analysis_method_id_fkey', 'result', type_='foreignkey')
    op.drop_constraint('result_epg_interpretation_method_id_fkey', 'result', type_='foreignkey')
    op.drop_column('result', 'dna_quantity')
    op.drop_column('result', 'pcr_method_id')
    op.drop_column('result', 'sample_input_volume_in_pcr')
    op.drop_column('result', 'dna_input_amount_in_pcr')
    op.drop_column('result', 'post_pcr_treatment_method_id')
    op.drop_column('result', 'ce_method_id')
    op.drop_column('result', 'epg_analysis_method_id')
    op.drop_column('result', 'epg_interpretation_method_id')
    op.drop_column('result', 'no_of_contributors')
    op.drop_column('result', 'mixture_proportion')
    op.drop_column('result', 'total_rfu')
    op.drop_column('result', 'total_no_of_alleles')


def downgrade() -> None:
    op.add_column('result', sa.Column('total_no_of_alleles', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('total_rfu', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('mixture_proportion', sa.Float(), nullable=True))
    op.add_column('result', sa.Column('no_of_contributors', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('epg_interpretation_method_id', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('epg_analysis_method_id', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('ce_method_id', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('post_pcr_treatment_method_id', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('dna_input_amount_in_pcr', sa.Float(), nullable=True))
    op.add_column('result', sa.Column('sample_input_volume_in_pcr', sa.Float(), nullable=True))
    op.add_column('result', sa.Column('pcr_method_id', sa.Integer(), nullable=True))
    op.add_column('result', sa.Column('dna_quantity', sa.Float(), nullable=True))

    op.create_foreign_key(
        'result_epg_interpretation_method_id_fkey', 'result', 'epg_interpretation_method',
        ['epg_interpretation_method_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'result_epg_analysis_method_id_fkey', 'result', 'epg_analysis_method',
        ['epg_analysis_method_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'result_ce_method_id_fkey', 'result', 'ce_method',
        ['ce_method_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'result_post_pcr_treatment_method_id_fkey', 'result', 'post_pcr_treatment_method',
        ['post_pcr_treatment_method_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'result_pcr_method_id_fkey', 'result', 'pcr_method',
        ['pcr_method_id'], ['id'], ondelete='SET NULL',
    )

    op.execute(
        """
        UPDATE result
        SET dna_quantity = pcr.dna_quantity,
            pcr_method_id = pcr.pcr_method_id,
            sample_input_volume_in_pcr = pcr.sample_input_volume_in_pcr,
            dna_input_amount_in_pcr = pcr.dna_input_amount_in_pcr,
            post_pcr_treatment_method_id = pcr.post_pcr_treatment_method_id,
            ce_method_id = pcr.ce_method_id,
            epg_analysis_method_id = pcr.epg_analysis_method_id,
            epg_interpretation_method_id = pcr.epg_interpretation_method_id,
            no_of_contributors = pcr.no_of_contributors,
            mixture_proportion = pcr.mixture_proportion,
            total_rfu = pcr.total_rfu,
            total_no_of_alleles = pcr.total_no_of_alleles
        FROM (
            SELECT DISTINCT ON (result_id) *
            FROM pcr
            ORDER BY result_id, id
        ) AS pcr
        WHERE result.id = pcr.result_id
        """
    )

    op.drop_index(op.f('ix_pcr_id'), table_name='pcr')
    op.drop_table('pcr')
