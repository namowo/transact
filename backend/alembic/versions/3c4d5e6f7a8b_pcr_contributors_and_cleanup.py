"""add pcr contributors, drop dna_quantity/mixture_proportion, convert dna_input to pg

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-10-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3c4d5e6f7a8b'
down_revision: Union[str, None] = '2b3c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ce_method', sa.Column('pcr_method_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'ce_method_pcr_method_id_fkey', 'ce_method', 'pcr_method',
        ['pcr_method_id'], ['id'], ondelete='SET NULL',
    )

    op.create_table(
        'pcr_contributor',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('pcr_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('individual_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('unknown_label', sa.String(), nullable=True),
        sa.Column('mixture_proportion', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['pcr_id'], ['pcr.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['individual_id'], ['individual.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pcr_contributor_id'), 'pcr_contributor', ['id'], unique=True)

    # Carry forward each PCR's existing single mixture_proportion as one
    # "UP1" contributor row before dropping the column, so existing data
    # isn't silently lost.
    op.execute(
        """
        INSERT INTO pcr_contributor (pcr_id, unknown_label, mixture_proportion)
        SELECT id, 'UP1', mixture_proportion
        FROM pcr
        WHERE mixture_proportion IS NOT NULL
        """
    )

    # dna_input_amount_in_pcr was recorded in ng; the lab enters this in pg.
    op.execute("UPDATE pcr SET dna_input_amount_in_pcr = dna_input_amount_in_pcr * 1000")

    op.drop_column('pcr', 'dna_quantity')
    op.drop_column('pcr', 'mixture_proportion')


def downgrade() -> None:
    op.add_column('pcr', sa.Column('mixture_proportion', sa.Float(), nullable=True))
    op.add_column('pcr', sa.Column('dna_quantity', sa.Float(), nullable=True))

    op.execute("UPDATE pcr SET dna_input_amount_in_pcr = dna_input_amount_in_pcr / 1000")

    op.execute(
        """
        UPDATE pcr
        SET mixture_proportion = pcr_contributor.mixture_proportion
        FROM (
            SELECT DISTINCT ON (pcr_id) *
            FROM pcr_contributor
            ORDER BY pcr_id, id
        ) AS pcr_contributor
        WHERE pcr.id = pcr_contributor.pcr_id
        """
    )

    op.drop_index(op.f('ix_pcr_contributor_id'), table_name='pcr_contributor')
    op.drop_table('pcr_contributor')

    op.drop_constraint('ce_method_pcr_method_id_fkey', 'ce_method', type_='foreignkey')
    op.drop_column('ce_method', 'pcr_method_id')
