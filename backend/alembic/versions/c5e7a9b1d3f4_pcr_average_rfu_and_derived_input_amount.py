"""pcr average rfu and derived dna input amount

Replaces pcr.total_rfu (integer) with pcr.average_rfu (decimal). Existing
totals are converted to total / total_no_of_alleles where the allele count
is known; otherwise they can't be converted and are dropped.

Also fills dna_input_amount_in_pcr (pg) from the result's DNA concentration
(ng/µl) x sample input volume (µl) x 1000 wherever both are known, matching
what the API now calculates on save.

Revision ID: c5e7a9b1d3f4
Revises: b4d6f8a0c2e3
Create Date: 2026-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e7a9b1d3f4'
down_revision: Union[str, None] = 'b4d6f8a0c2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pcr', sa.Column('average_rfu', sa.Float(), nullable=True))
    op.execute(
        """
        UPDATE pcr
        SET average_rfu = total_rfu::float / total_no_of_alleles
        WHERE total_rfu IS NOT NULL AND total_no_of_alleles > 0
        """
    )
    op.drop_column('pcr', 'total_rfu')

    op.execute(
        """
        UPDATE pcr
        SET dna_input_amount_in_pcr = result.dna_concentration * pcr.sample_input_volume_in_pcr * 1000
        FROM result
        WHERE pcr.result_id = result.id
          AND result.dna_concentration IS NOT NULL
          AND pcr.sample_input_volume_in_pcr IS NOT NULL
        """
    )


def downgrade() -> None:
    op.add_column('pcr', sa.Column('total_rfu', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE pcr
        SET total_rfu = round(average_rfu * total_no_of_alleles)
        WHERE average_rfu IS NOT NULL AND total_no_of_alleles IS NOT NULL
        """
    )
    op.drop_column('pcr', 'average_rfu')
