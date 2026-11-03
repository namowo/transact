"""source of dna many-to-many, item surface material category

Revision ID: b1c2d3e4f5a6
Revises: aa541a687a29
Create Date: 2026-10-26 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'aa541a687a29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Source of DNA: single FK -> many-to-many on both SurfaceTemplate and Surface ---
    op.create_table(
        'surface_template_source_of_dna',
        sa.Column('surface_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_of_dna_category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['surface_template_id'], ['surface_template.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_of_dna_category_id'], ['source_of_dna_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('surface_template_id', 'source_of_dna_category_id'),
    )
    op.create_table(
        'surface_source_of_dna',
        sa.Column('surface_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_of_dna_category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['surface_id'], ['surface.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_of_dna_category_id'], ['source_of_dna_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('surface_id', 'source_of_dna_category_id'),
    )

    # Backfill the association tables from the existing single FK columns
    # before dropping them.
    op.execute(
        "INSERT INTO surface_template_source_of_dna "
        "(surface_template_id, source_of_dna_category_id) "
        "SELECT id, source_of_dna_category_id FROM surface_template "
        "WHERE source_of_dna_category_id IS NOT NULL"
    )
    op.execute(
        "INSERT INTO surface_source_of_dna "
        "(surface_id, source_of_dna_category_id) "
        "SELECT id, source_of_dna_category_id FROM surface "
        "WHERE source_of_dna_category_id IS NOT NULL"
    )

    op.drop_constraint(
        'surface_template_source_of_dna_category_id_fkey', 'surface_template', type_='foreignkey'
    )
    op.drop_column('surface_template', 'source_of_dna_category_id')
    op.drop_constraint(
        'surface_source_of_dna_category_id_fkey', 'surface', type_='foreignkey'
    )
    op.drop_column('surface', 'source_of_dna_category_id')

    # --- Item surface material: new, independent category table + FK columns ---
    op.create_table(
        'item_surface_material_category',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_item_surface_material_category_id'),
        'item_surface_material_category',
        ['id'],
        unique=True,
    )

    op.add_column(
        'surface_template',
        sa.Column('item_surface_material_category_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'surface_template_item_surface_material_category_id_fkey',
        'surface_template',
        'item_surface_material_category',
        ['item_surface_material_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.add_column(
        'surface',
        sa.Column('item_surface_material_category_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'surface_item_surface_material_category_id_fkey',
        'surface',
        'item_surface_material_category',
        ['item_surface_material_category_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'surface_item_surface_material_category_id_fkey', 'surface', type_='foreignkey'
    )
    op.drop_column('surface', 'item_surface_material_category_id')
    op.drop_constraint(
        'surface_template_item_surface_material_category_id_fkey',
        'surface_template',
        type_='foreignkey',
    )
    op.drop_column('surface_template', 'item_surface_material_category_id')

    op.drop_index(op.f('ix_item_surface_material_category_id'), table_name='item_surface_material_category')
    op.drop_table('item_surface_material_category')

    op.add_column(
        'surface',
        sa.Column('source_of_dna_category_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'surface_template',
        sa.Column('source_of_dna_category_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Backfill an arbitrary one of the (possibly many) associated categories
    # per parent row.
    op.execute(
        "UPDATE surface_template SET source_of_dna_category_id = sub.source_of_dna_category_id "
        "FROM ("
        "  SELECT DISTINCT ON (surface_template_id) surface_template_id, source_of_dna_category_id "
        "  FROM surface_template_source_of_dna"
        ") AS sub "
        "WHERE sub.surface_template_id = surface_template.id"
    )
    op.execute(
        "UPDATE surface SET source_of_dna_category_id = sub.source_of_dna_category_id "
        "FROM ("
        "  SELECT DISTINCT ON (surface_id) surface_id, source_of_dna_category_id "
        "  FROM surface_source_of_dna"
        ") AS sub "
        "WHERE sub.surface_id = surface.id"
    )

    op.create_foreign_key(
        'surface_template_source_of_dna_category_id_fkey',
        'surface_template',
        'source_of_dna_category',
        ['source_of_dna_category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'surface_source_of_dna_category_id_fkey',
        'surface',
        'source_of_dna_category',
        ['source_of_dna_category_id'],
        ['id'],
        ondelete='SET NULL',
    )

    op.drop_table('surface_source_of_dna')
    op.drop_table('surface_template_source_of_dna')
