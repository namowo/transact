"""link item categories, globalize author, atomize shedding propensity determination

Revision ID: 005b0c0560e8
Revises: 683ac9981324
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005b0c0560e8'
down_revision: Union[str, None] = '683ac9981324'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NAME_ONLY_TABLES = [
    'restriction_prior_to_sampling',
    'monitored_transfer_factor',
    'shedder_test',
    'classification_criteria',
    'classification_scheme',
]


def upgrade() -> None:
    # --- item_subcategory / item_parts_category -> item_category FK ---
    op.add_column('item_subcategory', sa.Column('item_category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'item_subcategory_item_category_id_fkey',
        'item_subcategory',
        'item_category',
        ['item_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.add_column('item_parts_category', sa.Column('item_category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'item_parts_category_item_category_id_fkey',
        'item_parts_category',
        'item_category',
        ['item_category_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # --- type_of_swab_category: bring back per-row supplier catalogue fields ---
    op.add_column(
        'type_of_swab_category',
        sa.Column('catalogue_number_of_supplier', sa.String(), nullable=True),
    )
    op.add_column(
        'type_of_swab_category',
        sa.Column('full_name_as_by_supplier', sa.String(), nullable=True),
    )

    # --- author: drop per-study ownership, make it a globally reusable entity ---
    op.create_table(
        'study_author',
        sa.Column('study_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['author.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('study_id', 'author_id'),
    )
    op.execute(
        "INSERT INTO study_author (study_id, author_id, position) "
        "SELECT study_id, id, position FROM author"
    )
    op.drop_constraint('author_study_id_fkey', 'author', type_='foreignkey')
    op.drop_column('author', 'study_id')
    op.drop_column('author', 'position')

    # --- new lookup tables backing an atomized DeterminationOfSheddingPropensityCategory ---
    for table_name in NAME_ONLY_TABLES:
        op.create_table(
            table_name,
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f(f'ix_{table_name}_id'), table_name, ['id'], unique=True)

    op.create_table(
        'determination_of_shedding_propensity_category_author',
        sa.Column('determination_of_shedding_propensity_category_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['determination_of_shedding_propensity_category_id'],
            ['determination_of_shedding_propensity_category.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(['author_id'], ['author.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('determination_of_shedding_propensity_category_id', 'author_id'),
    )

    op.create_table(
        'determination_of_shedding_propensity_category_restriction',
        sa.Column('determination_of_shedding_propensity_category_id', sa.Integer(), nullable=False),
        sa.Column('restriction_prior_to_sampling_id', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Interval(), nullable=True),
        sa.ForeignKeyConstraint(
            ['determination_of_shedding_propensity_category_id'],
            ['determination_of_shedding_propensity_category.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['restriction_prior_to_sampling_id'], ['restriction_prior_to_sampling.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint(
            'determination_of_shedding_propensity_category_id', 'restriction_prior_to_sampling_id'
        ),
    )

    op.create_table(
        'det_shedding_propensity_category_transfer_factor',
        sa.Column('determination_of_shedding_propensity_category_id', sa.Integer(), nullable=False),
        sa.Column('monitored_transfer_factor_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['determination_of_shedding_propensity_category_id'],
            ['determination_of_shedding_propensity_category.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['monitored_transfer_factor_id'], ['monitored_transfer_factor.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint(
            'determination_of_shedding_propensity_category_id', 'monitored_transfer_factor_id'
        ),
    )

    op.create_table(
        'determination_of_shedding_propensity_category_shedder_test',
        sa.Column('determination_of_shedding_propensity_category_id', sa.Integer(), nullable=False),
        sa.Column('shedder_test_id', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Interval(), nullable=True),
        sa.ForeignKeyConstraint(
            ['determination_of_shedding_propensity_category_id'],
            ['determination_of_shedding_propensity_category.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(['shedder_test_id'], ['shedder_test.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('determination_of_shedding_propensity_category_id', 'shedder_test_id'),
    )

    # --- determination_of_shedding_propensity_category: drop atomized text
    # columns, add FKs to the new lookup tables ---
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('classification_criteria_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('classification_scheme_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'det_shed_propensity_cat_classification_criteria_id_fkey',
        'determination_of_shedding_propensity_category',
        'classification_criteria',
        ['classification_criteria_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'det_shed_propensity_cat_classification_scheme_id_fkey',
        'determination_of_shedding_propensity_category',
        'classification_scheme',
        ['classification_scheme_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.alter_column(
        'determination_of_shedding_propensity_category',
        'number_of_participants',
        type_=sa.Integer(),
        postgresql_using='number_of_participants::integer',
    )
    op.alter_column(
        'determination_of_shedding_propensity_category',
        'replicates',
        type_=sa.Integer(),
        postgresql_using='replicates::integer',
    )
    op.drop_column('determination_of_shedding_propensity_category', 'authors')
    op.drop_column('determination_of_shedding_propensity_category', 'restrictions_prior_to_sampling')
    op.drop_column('determination_of_shedding_propensity_category', 'monitored_transfer_factors')
    op.drop_column('determination_of_shedding_propensity_category', 'shedder_test')
    op.drop_column('determination_of_shedding_propensity_category', 'classification_criteria')
    op.drop_column('determination_of_shedding_propensity_category', 'classification_scheme')


def downgrade() -> None:
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('classification_scheme', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('classification_criteria', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('shedder_test', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('monitored_transfer_factors', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('restrictions_prior_to_sampling', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'determination_of_shedding_propensity_category',
        sa.Column('authors', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.alter_column(
        'determination_of_shedding_propensity_category',
        'replicates',
        type_=sa.String(),
        postgresql_using='replicates::varchar',
    )
    op.alter_column(
        'determination_of_shedding_propensity_category',
        'number_of_participants',
        type_=sa.String(),
        postgresql_using='number_of_participants::varchar',
    )
    op.drop_constraint(
        'det_shed_propensity_cat_classification_scheme_id_fkey',
        'determination_of_shedding_propensity_category',
        type_='foreignkey',
    )
    op.drop_constraint(
        'det_shed_propensity_cat_classification_criteria_id_fkey',
        'determination_of_shedding_propensity_category',
        type_='foreignkey',
    )
    op.drop_column('determination_of_shedding_propensity_category', 'classification_scheme_id')
    op.drop_column('determination_of_shedding_propensity_category', 'classification_criteria_id')

    op.drop_table('determination_of_shedding_propensity_category_shedder_test')
    op.drop_table('det_shedding_propensity_category_transfer_factor')
    op.drop_table('determination_of_shedding_propensity_category_restriction')
    op.drop_table('determination_of_shedding_propensity_category_author')

    for table_name in reversed(NAME_ONLY_TABLES):
        op.drop_index(op.f(f'ix_{table_name}_id'), table_name=table_name)
        op.drop_table(table_name)

    op.add_column(
        'author', sa.Column('position', sa.Integer(), autoincrement=False, nullable=False, server_default='0')
    )
    op.add_column('author', sa.Column('study_id', sa.Integer(), autoincrement=False, nullable=True))
    op.execute(
        "UPDATE author SET study_id = study_author.study_id, position = study_author.position "
        "FROM study_author WHERE study_author.author_id = author.id"
    )
    op.alter_column('author', 'study_id', nullable=False)
    op.alter_column('author', 'position', server_default=None)
    op.create_foreign_key(
        'author_study_id_fkey', 'author', 'study', ['study_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_table('study_author')

    op.drop_column('type_of_swab_category', 'full_name_as_by_supplier')
    op.drop_column('type_of_swab_category', 'catalogue_number_of_supplier')

    op.drop_constraint('item_parts_category_item_category_id_fkey', 'item_parts_category', type_='foreignkey')
    op.drop_column('item_parts_category', 'item_category_id')
    op.drop_constraint('item_subcategory_item_category_id_fkey', 'item_subcategory', type_='foreignkey')
    op.drop_column('item_subcategory', 'item_category_id')
