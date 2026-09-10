"""convert remaining tables to uuid primary keys

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a8
Create Date: 2026-08-31 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b2c3d4e5f6a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables whose integer `id` primary key is converted to UUID, in FK-safe order.
ID_TABLES = [
    'activity_category',
    'application_analytical_threshold',
    'author',
    'body_part_condition_category',
    'ce_device',
    'classification_criteria',
    'classification_scheme',
    'condition_of_item_part_category',
    'cutting_device',
    'degradation_category',
    'disturbance_category',
    'dna_shedding_propensity_category',
    'dye_set',
    'experience_level',
    'friction_applied_estiamte',
    'genotyping_software',
    'geographic_location_category',
    'inhibition_category',
    'item_category',
    'laboratory',
    'location_of_body_category',
    'manufacturer',
    'monitored_transfer_factor',
    'pcr_kit',
    'picking_device',
    'platform',
    'polymer',
    'pressure_estimate',
    'principle_of_extraction_method_category',
    'principle_of_quant_method_category',
    'quantification_kit',
    'recovery_set',
    'restriction_prior_to_sampling',
    'scenario_category',
    'scraping_device',
    'sex',
    'shedder_test',
    'size_standard',
    'skin_disease_category',
    'source_of_dna_category',
    'statistical_software',
    'stutter_filter',
    'supplier',
    'surface_material_category',
    'swabbing_technique_category',
    'thermocycler',
    'type_of_formamide',
    'type_of_tape',
    'user_token',
    'vacuum_device',
    'webauthn_challenge',
    'webauthn_credential',
    'wetting_agent',
    'determination_of_shedding_propensity_category',
    'condition_during_contact',
    'item_parts_category',
    'item_subcategory',
    'epg_analysis_method',
    'lab_membership_request',
    'post_pcr_treatment_method',
    'study',
    'extraction_method',
    'quantification_method',
    'epg_interpretation_method',
    'cutting_method',
    'picking_method',
    'scraping_method',
    'type_of_swab_category',
    'pcr_method',
    'ce_method',
    'tape_method',
    'vacuum_method',
    'individual',
    'item',
    'persistence',
    'scenario',
    'swab_method',
    'surface_template',
    'sampling_method',
    'contact_template',
    'surface',
    'contact',
    'recovery',
    'result',
    'pcr',
]

# Every FK column across the schema that references one of ID_TABLES (or `user`,
# already UUID) and is not yet UUID. (table, column, ref_table, nullable, ondelete)
FK_COLUMNS = [
    ('user', 'laboratory_id', 'laboratory', True, 'RESTRICT'),
    ('ce_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('ce_method', 'ce_device_id', 'ce_device', True, 'SET NULL'),
    ('ce_method', 'polymer_id', 'polymer', True, 'SET NULL'),
    ('ce_method', 'dye_set_id', 'dye_set', True, 'SET NULL'),
    ('ce_method', 'type_of_formamide_id', 'type_of_formamide', True, 'SET NULL'),
    ('ce_method', 'size_standard_id', 'size_standard', True, 'SET NULL'),
    ('condition_during_contact', 'disturbance_category_id', 'disturbance_category', True, 'SET NULL'),
    ('condition_during_contact', 'geographic_location_category_id', 'geographic_location_category', True, 'SET NULL'),
    ('contact', 'contact_template_id', 'contact_template', False, 'CASCADE'),
    ('contact', 'donor_surface_id', 'surface', True, 'SET NULL'),
    ('contact', 'recipient_surface_id', 'surface', True, 'SET NULL'),
    ('contact', 'pressure_estimate_id', 'pressure_estimate', True, 'SET NULL'),
    ('contact', 'friction_applied_estimate_id', 'friction_applied_estiamte', True, 'SET NULL'),
    ('contact', 'activity_category_id', 'activity_category', True, 'SET NULL'),
    ('contact', 'condition_during_contact_id', 'condition_during_contact', True, 'SET NULL'),
    ('surface', 'surface_template_id', 'surface_template', True, 'SET NULL'),
    ('surface', 'individual_id', 'individual', True, 'SET NULL'),
    ('surface', 'location_of_body_category_id', 'location_of_body_category', True, 'SET NULL'),
    ('surface', 'body_part_condition_category_id', 'body_part_condition_category', True, 'SET NULL'),
    ('surface', 'item_parts_category_id', 'item_parts_category', True, 'SET NULL'),
    ('surface', 'condition_of_item_part_category_id', 'condition_of_item_part_category', True, 'SET NULL'),
    ('surface', 'surface_material_category_id', 'surface_material_category', True, 'SET NULL'),
    ('surface', 'source_of_dna_category_id', 'source_of_dna_category', True, 'SET NULL'),
    ('surface_template', 'location_of_body_category_id', 'location_of_body_category', True, 'SET NULL'),
    ('surface_template', 'body_part_condition_category_id', 'body_part_condition_category', True, 'SET NULL'),
    ('surface_template', 'item_id', 'item', True, 'SET NULL'),
    ('surface_template', 'item_parts_category_id', 'item_parts_category', True, 'SET NULL'),
    ('surface_template', 'condition_of_item_part_category_id', 'condition_of_item_part_category', True, 'SET NULL'),
    ('surface_template', 'surface_material_category_id', 'surface_material_category', True, 'SET NULL'),
    ('surface_template', 'source_of_dna_category_id', 'source_of_dna_category', True, 'SET NULL'),
    ('item', 'item_category_id', 'item_category', True, 'SET NULL'),
    ('item', 'item_subcategory_id', 'item_subcategory', True, 'SET NULL'),
    ('item_subcategory', 'item_category_id', 'item_category', True, 'SET NULL'),
    ('item_parts_category', 'item_category_id', 'item_category', True, 'SET NULL'),
    ('individual', 'sex_id', 'sex', True, 'SET NULL'),
    ('individual', 'dna_shedding_propensity_category_id', 'dna_shedding_propensity_category', True, 'SET NULL'),
    ('individual', 'skin_disease_category_id', 'skin_disease_category', True, 'SET NULL'),
    ('individual', 'determination_of_shedding_propensity_category_id', 'determination_of_shedding_propensity_category', True, 'SET NULL'),
    ('determination_of_shedding_propensity_category_author', 'determination_of_shedding_propensity_category_id', 'determination_of_shedding_propensity_category', False, 'CASCADE'),
    ('determination_of_shedding_propensity_category_author', 'author_id', 'author', False, 'CASCADE'),
    ('det_shedding_propensity_category_transfer_factor', 'determination_of_shedding_propensity_category_id', 'determination_of_shedding_propensity_category', False, 'CASCADE'),
    ('det_shedding_propensity_category_transfer_factor', 'monitored_transfer_factor_id', 'monitored_transfer_factor', False, 'CASCADE'),
    ('determination_of_shedding_propensity_category', 'classification_criteria_id', 'classification_criteria', True, 'SET NULL'),
    ('determination_of_shedding_propensity_category', 'classification_scheme_id', 'classification_scheme', True, 'SET NULL'),
    ('determination_of_shedding_propensity_category_restriction', 'determination_of_shedding_propensity_category_id', 'determination_of_shedding_propensity_category', False, 'CASCADE'),
    ('determination_of_shedding_propensity_category_restriction', 'restriction_prior_to_sampling_id', 'restriction_prior_to_sampling', False, 'CASCADE'),
    ('determination_of_shedding_propensity_category_shedder_test', 'determination_of_shedding_propensity_category_id', 'determination_of_shedding_propensity_category', False, 'CASCADE'),
    ('determination_of_shedding_propensity_category_shedder_test', 'shedder_test_id', 'shedder_test', False, 'CASCADE'),
    ('scenario_contact_template', 'scenario_id', 'scenario', False, 'CASCADE'),
    ('scenario_contact_template', 'contact_template_id', 'contact_template', False, 'CASCADE'),
    ('contact_template', 'donor_surface_template_id', 'surface_template', True, 'SET NULL'),
    ('contact_template', 'recipient_surface_template_id', 'surface_template', True, 'SET NULL'),
    ('contact_template', 'pressure_estimate_id', 'pressure_estimate', True, 'SET NULL'),
    ('contact_template', 'friction_applied_estimate_id', 'friction_applied_estiamte', True, 'SET NULL'),
    ('contact_template', 'activity_category_id', 'activity_category', True, 'SET NULL'),
    ('contact_template', 'condition_during_contact_id', 'condition_during_contact', True, 'SET NULL'),
    ('cutting_method', 'cutting_device_id', 'cutting_device', True, 'SET NULL'),
    ('cutting_method', 'supplier_id', 'supplier', True, 'SET NULL'),
    ('epg_analysis_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('epg_analysis_method', 'genotyping_software_id', 'genotyping_software', True, 'SET NULL'),
    ('epg_interpretation_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('epg_interpretation_method', 'statistical_software_id', 'statistical_software', True, 'SET NULL'),
    ('epg_interpretation_method', 'application_analytical_threshold_id', 'application_analytical_threshold', True, 'SET NULL'),
    ('epg_interpretation_method', 'stutter_filter_id', 'stutter_filter', True, 'SET NULL'),
    ('extraction_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('extraction_method', 'principle_of_extraction_method_category_id', 'principle_of_extraction_method_category', True, 'SET NULL'),
    ('extraction_method', 'extraction_platform_id', 'platform', True, 'SET NULL'),
    ('lab_membership_request', 'laboratory_id', 'laboratory', False, 'CASCADE'),
    ('pcr', 'result_id', 'result', False, 'CASCADE'),
    ('pcr', 'pcr_method_id', 'pcr_method', True, 'SET NULL'),
    ('pcr', 'post_pcr_treatment_method_id', 'post_pcr_treatment_method', True, 'SET NULL'),
    ('pcr', 'ce_method_id', 'ce_method', True, 'SET NULL'),
    ('pcr', 'epg_analysis_method_id', 'epg_analysis_method', True, 'SET NULL'),
    ('pcr', 'epg_interpretation_method_id', 'epg_interpretation_method', True, 'SET NULL'),
    ('pcr_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('pcr_method', 'pcr_kit_id', 'pcr_kit', True, 'SET NULL'),
    ('pcr_method', 'thermocycler_id', 'thermocycler', True, 'SET NULL'),
    ('post_pcr_treatment_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('persistence', 'owning_study_id', 'study', True, 'SET NULL'),
    ('persistence', 'disturbance_category_id', 'disturbance_category', True, 'SET NULL'),
    ('persistence', 'geographic_location_category_id', 'geographic_location_category', True, 'SET NULL'),
    ('study', 'laboratory_id', 'laboratory', False, 'SET NULL'),
    ('study_author', 'study_id', 'study', False, 'CASCADE'),
    ('study_author', 'author_id', 'author', False, 'CASCADE'),
    ('picking_method', 'picking_device_id', 'picking_device', True, 'SET NULL'),
    ('picking_method', 'supplier_id', 'supplier', True, 'SET NULL'),
    ('quantification_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('quantification_method', 'principle_of_quant_method_category_id', 'principle_of_quant_method_category', True, 'SET NULL'),
    ('quantification_method', 'kit_id', 'quantification_kit', True, 'SET NULL'),
    ('quantification_method', 'manufacturer_id', 'manufacturer', True, 'SET NULL'),
    ('quantification_method', 'platform_id', 'platform', True, 'SET NULL'),
    ('recovery', 'study_id', 'study', True, 'SET NULL'),
    ('recovery', 'recovery_set_id', 'recovery_set', True, 'SET NULL'),
    ('recovery', 'surface_id', 'surface', True, 'SET NULL'),
    ('recovery', 'sampling_method_id', 'sampling_method', True, 'SET NULL'),
    ('recovery', 'extraction_method_id', 'extraction_method', True, 'SET NULL'),
    ('recovery', 'experience_level_of_sampler_id', 'experience_level', True, 'SET NULL'),
    ('sampling_method', 'laboratory_id', 'laboratory', True, 'SET NULL'),
    ('sampling_method', 'swab_method_id', 'swab_method', True, 'SET NULL'),
    ('sampling_method', 'tape_method_id', 'tape_method', True, 'SET NULL'),
    ('sampling_method', 'vacuum_method_id', 'vacuum_method', True, 'SET NULL'),
    ('sampling_method', 'cutting_method_id', 'cutting_method', True, 'SET NULL'),
    ('sampling_method', 'scraping_method_id', 'scraping_method', True, 'SET NULL'),
    ('sampling_method', 'picking_method_id', 'picking_method', True, 'SET NULL'),
    ('swab_method', 'wetting_agent_id', 'wetting_agent', True, 'SET NULL'),
    ('swab_method', 'type_of_swab_category_id', 'type_of_swab_category', True, 'SET NULL'),
    ('swab_method', 'swabbing_technique_category_id', 'swabbing_technique_category', True, 'SET NULL'),
    ('type_of_swab_category', 'supplier_id', 'supplier', True, 'SET NULL'),
    ('tape_method', 'type_of_tape_id', 'type_of_tape', True, 'SET NULL'),
    ('tape_method', 'supplier_id', 'supplier', True, 'SET NULL'),
    ('vacuum_method', 'vacuum_device_id', 'vacuum_device', True, 'SET NULL'),
    ('vacuum_method', 'supplier_id', 'supplier', True, 'SET NULL'),
    ('scraping_method', 'scraping_device_id', 'scraping_device', True, 'SET NULL'),
    ('scraping_method', 'supplier_id', 'supplier', True, 'SET NULL'),
    ('result', 'quantification_method_id', 'quantification_method', True, 'SET NULL'),
    ('result', 'recovery_id', 'recovery', True, 'SET NULL'),
    ('result', 'degradation_category_id', 'degradation_category', True, 'SET NULL'),
    ('result', 'inhibition_category_id', 'inhibition_category', True, 'SET NULL'),
    ('study_scenario', 'study_id', 'study', False, 'CASCADE'),
    ('study_scenario', 'scenario_id', 'scenario', False, 'CASCADE'),
    ('scenario_persistence', 'scenario_id', 'scenario', False, 'CASCADE'),
    ('scenario_persistence', 'persistence_id', 'persistence', False, 'CASCADE'),
    ('scenario', 'scenario_category_id', 'scenario_category', False, 'SET NULL'),
    ('scenario', 'owning_study_id', 'study', True, 'SET NULL'),
]


def upgrade() -> None:
    # 1. Add a new UUID id column (default gen_random_uuid()) to every converted table
    #    and backfill it.
    for table in ID_TABLES:
        op.add_column(
            table,
            sa.Column(
                'new_id',
                postgresql.UUID(as_uuid=True),
                server_default=sa.text('gen_random_uuid()'),
                nullable=True,
            ),
        )
        op.execute(f'UPDATE "{table}" SET new_id = gen_random_uuid() WHERE new_id IS NULL')

    # 2. Add a new UUID FK column to every table with a column referencing a converted
    #    table, and backfill it by joining the referenced table's new_id (or id, if the
    #    referenced table is `user`, already UUID from the prior migration).
    for table, column, ref_table, _nullable, _ondelete in FK_COLUMNS:
        new_column = f'new_{column}'
        op.add_column(
            table, sa.Column(new_column, postgresql.UUID(as_uuid=True), nullable=True)
        )
        ref_id_expr = 'new_id' if ref_table in ID_TABLES else 'id'
        op.execute(
            f'UPDATE "{table}" t SET {new_column} = r.new_id_or_id '
            f'FROM (SELECT id, {ref_id_expr} AS new_id_or_id FROM "{ref_table}") r '
            f'WHERE t.{column} = r.id'
        )

    # 3. Drop old FK constraints. Postgres auto-generates (and silently truncates to 63
    #    bytes) names of the form <table>_<column>_fkey, so look the real name up instead
    #    of re-deriving it, which would break for the schema's longer table/column names.
    for table, column, _ref_table, _nullable, _ondelete in FK_COLUMNS:
        op.execute(
            f"""
            DO $$
            DECLARE
                fk_name text;
            BEGIN
                SELECT tc.constraint_name INTO fk_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.table_name = '{table}'
                    AND tc.constraint_type = 'FOREIGN KEY'
                    AND kcu.column_name = '{column}'
                    AND tc.table_schema = current_schema();
                IF fk_name IS NOT NULL THEN
                    EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', '{table}', fk_name);
                END IF;
            END $$;
            """
        )

    # 4. Drop old integer FK columns and rename the new UUID columns into place.
    for table, column, _ref_table, nullable, _ondelete in FK_COLUMNS:
        op.drop_column(table, column)
        op.alter_column(table, f'new_{column}', new_column_name=column)
        if not nullable:
            op.alter_column(table, column, nullable=False)

    # 5. Drop old integer PKs/indexes and rename the new UUID id columns into place.
    for table in ID_TABLES:
        op.drop_constraint(f'{table}_pkey', table, type_='primary')
        op.execute(f'DROP INDEX IF EXISTS "ix_{table}_id"')
        op.drop_column(table, 'id')
        op.alter_column(table, 'new_id', new_column_name='id')
        op.alter_column(table, 'id', nullable=False)
        op.create_primary_key(f'{table}_pkey', table, ['id'])
        op.create_index(f'ix_{table}_id', table, ['id'], unique=False)

    # 6. Recreate FK constraints for every converted FK column. Pass None for the
    #    constraint name so Postgres auto-generates (and truncates if needed) it the same
    #    way it did when the column was first created.
    for table, column, ref_table, _nullable, ondelete in FK_COLUMNS:
        op.create_foreign_key(
            None, table, ref_table, [column], ['id'], ondelete=ondelete,
        )

    # No non-default (unique/partial) indexes existed on any of the converted FK or id
    # columns besides the ones already recreated in the previous migration, so no further
    # index recreation is needed here.


def downgrade() -> None:
    raise NotImplementedError('Downgrade from UUID ids is not supported.')
