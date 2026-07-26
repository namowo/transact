"""normalize string lookup fields into dedicated tables

Revision ID: f1a2b3c4d5e6
Revises: 3b4c5d6e7f8a
Create Date: 2026-07-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '3b4c5d6e7f8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NAME_ONLY_TABLES = [
    'sex',
    'dna_shedding_propensity_category',
    'pcr_kit',
    'thermocycler',
    'ce_device',
    'polymer',
    'dye_set',
    'type_of_formamide',
    'size_standard',
    'genotyping_software',
    'statistical_software',
    'quantification_kit',
    'manufacturer',
    'platform',
    'wetting_agent',
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

    op.create_table(
        'supplier',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('catalogue_number_of_supplier', sa.String(), nullable=True),
        sa.Column('full_name_as_by_supplier', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_supplier_id'), 'supplier', ['id'], unique=True)

    # individual: sex, dna_shedding_propensity -> FK lookups
    op.add_column('individual', sa.Column('sex_id', sa.Integer(), nullable=True))
    op.add_column(
        'individual',
        sa.Column('dna_shedding_propensity_category_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'individual_sex_id_fkey', 'individual', 'sex', ['sex_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'individual_dna_shedding_propensity_category_id_fkey',
        'individual',
        'dna_shedding_propensity_category',
        ['dna_shedding_propensity_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('individual', 'sex')
    op.drop_column('individual', 'dna_shedding_propensity')

    # pcr_method: pcr_kit, thermocycler -> FK lookups
    op.add_column('pcr_method', sa.Column('pcr_kit_id', sa.Integer(), nullable=True))
    op.add_column('pcr_method', sa.Column('thermocycler_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'pcr_method_pcr_kit_id_fkey', 'pcr_method', 'pcr_kit', ['pcr_kit_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'pcr_method_thermocycler_id_fkey',
        'pcr_method',
        'thermocycler',
        ['thermocycler_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('pcr_method', 'pcr_kit')
    op.drop_column('pcr_method', 'thermocycler')

    # ce_method: ce_device, polymer, dye_set, type_of_formamide, size_standard -> FK lookups
    op.add_column('ce_method', sa.Column('ce_device_id', sa.Integer(), nullable=True))
    op.add_column('ce_method', sa.Column('polymer_id', sa.Integer(), nullable=True))
    op.add_column('ce_method', sa.Column('dye_set_id', sa.Integer(), nullable=True))
    op.add_column('ce_method', sa.Column('type_of_formamide_id', sa.Integer(), nullable=True))
    op.add_column('ce_method', sa.Column('size_standard_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'ce_method_ce_device_id_fkey', 'ce_method', 'ce_device', ['ce_device_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'ce_method_polymer_id_fkey', 'ce_method', 'polymer', ['polymer_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'ce_method_dye_set_id_fkey', 'ce_method', 'dye_set', ['dye_set_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'ce_method_type_of_formamide_id_fkey',
        'ce_method',
        'type_of_formamide',
        ['type_of_formamide_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'ce_method_size_standard_id_fkey',
        'ce_method',
        'size_standard',
        ['size_standard_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('ce_method', 'ce_device')
    op.drop_column('ce_method', 'polymer')
    op.drop_column('ce_method', 'dye_set')
    op.drop_column('ce_method', 'type_of_formamide')
    op.drop_column('ce_method', 'size_standard')

    # epg_analysis_method: genotyping_software -> FK lookup
    op.add_column('epg_analysis_method', sa.Column('genotyping_software_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'epg_analysis_method_genotyping_software_id_fkey',
        'epg_analysis_method',
        'genotyping_software',
        ['genotyping_software_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('epg_analysis_method', 'genotyping_software')

    # epg_interpretation_method: statistical_software -> FK lookup
    op.add_column(
        'epg_interpretation_method', sa.Column('statistical_software_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'epg_interpretation_method_statistical_software_id_fkey',
        'epg_interpretation_method',
        'statistical_software',
        ['statistical_software_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('epg_interpretation_method', 'statistical_software')

    # quantification_method: kit, manufacturer, platform -> FK lookups
    op.add_column('quantification_method', sa.Column('kit_id', sa.Integer(), nullable=True))
    op.add_column('quantification_method', sa.Column('manufacturer_id', sa.Integer(), nullable=True))
    op.add_column('quantification_method', sa.Column('platform_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'quantification_method_kit_id_fkey',
        'quantification_method',
        'quantification_kit',
        ['kit_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'quantification_method_manufacturer_id_fkey',
        'quantification_method',
        'manufacturer',
        ['manufacturer_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'quantification_method_platform_id_fkey',
        'quantification_method',
        'platform',
        ['platform_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('quantification_method', 'kit')
    op.drop_column('quantification_method', 'manufacturer')
    op.drop_column('quantification_method', 'platform')

    # extraction_method: extraction_platform -> FK lookup (shared platform table)
    op.add_column('extraction_method', sa.Column('extraction_platform_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'extraction_method_extraction_platform_id_fkey',
        'extraction_method',
        'platform',
        ['extraction_platform_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('extraction_method', 'extraction_platform')

    # swab_method: wetting_agent -> FK lookup
    op.add_column('swab_method', sa.Column('wetting_agent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'swab_method_wetting_agent_id_fkey',
        'swab_method',
        'wetting_agent',
        ['wetting_agent_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.drop_column('swab_method', 'wetting_agent')

    # type_of_swab_category, cutting_method, picking_method, scraping_method,
    # tape_method, vacuum_method: supplier/catalogue_number_of_supplier/
    # full_name_as_by_supplier -> shared supplier FK lookup
    for table_name in [
        'type_of_swab_category',
        'cutting_method',
        'picking_method',
        'scraping_method',
        'tape_method',
        'vacuum_method',
    ]:
        op.add_column(table_name, sa.Column('supplier_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            f'{table_name}_supplier_id_fkey',
            table_name,
            'supplier',
            ['supplier_id'],
            ['id'],
            ondelete='SET NULL',
        )
        op.drop_column(table_name, 'catalogue_number_of_supplier')
        op.drop_column(table_name, 'full_name_as_by_supplier')
        op.drop_column(table_name, 'supplier')


def downgrade() -> None:
    for table_name in [
        'type_of_swab_category',
        'cutting_method',
        'picking_method',
        'scraping_method',
        'tape_method',
        'vacuum_method',
    ]:
        op.add_column(table_name, sa.Column('supplier', sa.VARCHAR(), autoincrement=False, nullable=True))
        op.add_column(
            table_name,
            sa.Column('full_name_as_by_supplier', sa.VARCHAR(), autoincrement=False, nullable=True),
        )
        op.add_column(
            table_name,
            sa.Column('catalogue_number_of_supplier', sa.VARCHAR(), autoincrement=False, nullable=True),
        )
        op.drop_constraint(f'{table_name}_supplier_id_fkey', table_name, type_='foreignkey')
        op.drop_column(table_name, 'supplier_id')

    op.add_column('swab_method', sa.Column('wetting_agent', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('swab_method_wetting_agent_id_fkey', 'swab_method', type_='foreignkey')
    op.drop_column('swab_method', 'wetting_agent_id')

    op.add_column(
        'extraction_method', sa.Column('extraction_platform', sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(
        'extraction_method_extraction_platform_id_fkey', 'extraction_method', type_='foreignkey'
    )
    op.drop_column('extraction_method', 'extraction_platform_id')

    op.add_column('quantification_method', sa.Column('platform', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('quantification_method', sa.Column('manufacturer', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('quantification_method', sa.Column('kit', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('quantification_method_platform_id_fkey', 'quantification_method', type_='foreignkey')
    op.drop_constraint('quantification_method_manufacturer_id_fkey', 'quantification_method', type_='foreignkey')
    op.drop_constraint('quantification_method_kit_id_fkey', 'quantification_method', type_='foreignkey')
    op.drop_column('quantification_method', 'platform_id')
    op.drop_column('quantification_method', 'manufacturer_id')
    op.drop_column('quantification_method', 'kit_id')

    op.add_column(
        'epg_interpretation_method',
        sa.Column('statistical_software', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(
        'epg_interpretation_method_statistical_software_id_fkey',
        'epg_interpretation_method',
        type_='foreignkey',
    )
    op.drop_column('epg_interpretation_method', 'statistical_software_id')

    op.add_column(
        'epg_analysis_method', sa.Column('genotyping_software', sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(
        'epg_analysis_method_genotyping_software_id_fkey', 'epg_analysis_method', type_='foreignkey'
    )
    op.drop_column('epg_analysis_method', 'genotyping_software_id')

    op.add_column('ce_method', sa.Column('size_standard', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('ce_method', sa.Column('type_of_formamide', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('ce_method', sa.Column('dye_set', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('ce_method', sa.Column('polymer', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('ce_method', sa.Column('ce_device', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('ce_method_size_standard_id_fkey', 'ce_method', type_='foreignkey')
    op.drop_constraint('ce_method_type_of_formamide_id_fkey', 'ce_method', type_='foreignkey')
    op.drop_constraint('ce_method_dye_set_id_fkey', 'ce_method', type_='foreignkey')
    op.drop_constraint('ce_method_polymer_id_fkey', 'ce_method', type_='foreignkey')
    op.drop_constraint('ce_method_ce_device_id_fkey', 'ce_method', type_='foreignkey')
    op.drop_column('ce_method', 'size_standard_id')
    op.drop_column('ce_method', 'type_of_formamide_id')
    op.drop_column('ce_method', 'dye_set_id')
    op.drop_column('ce_method', 'polymer_id')
    op.drop_column('ce_method', 'ce_device_id')

    op.add_column('pcr_method', sa.Column('thermocycler', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('pcr_method', sa.Column('pcr_kit', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('pcr_method_thermocycler_id_fkey', 'pcr_method', type_='foreignkey')
    op.drop_constraint('pcr_method_pcr_kit_id_fkey', 'pcr_method', type_='foreignkey')
    op.drop_column('pcr_method', 'thermocycler_id')
    op.drop_column('pcr_method', 'pcr_kit_id')

    op.add_column(
        'individual', sa.Column('dna_shedding_propensity', sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.add_column('individual', sa.Column('sex', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(
        'individual_dna_shedding_propensity_category_id_fkey', 'individual', type_='foreignkey'
    )
    op.drop_constraint('individual_sex_id_fkey', 'individual', type_='foreignkey')
    op.drop_column('individual', 'dna_shedding_propensity_category_id')
    op.drop_column('individual', 'sex_id')

    op.drop_index(op.f('ix_supplier_id'), table_name='supplier')
    op.drop_table('supplier')

    for table_name in reversed(NAME_ONLY_TABLES):
        op.drop_index(op.f(f'ix_{table_name}_id'), table_name=table_name)
        op.drop_table(table_name)
