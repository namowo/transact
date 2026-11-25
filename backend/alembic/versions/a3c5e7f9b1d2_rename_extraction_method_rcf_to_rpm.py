"""rename extraction method rcf to rpm

Revision ID: a3c5e7f9b1d2
Revises: fcf2d249fcdc
Create Date: 2026-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a3c5e7f9b1d2'
down_revision: Union[str, None] = 'fcf2d249fcdc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('extraction_method', 'rcf', new_column_name='rpm')


def downgrade() -> None:
    op.alter_column('extraction_method', 'rpm', new_column_name='rcf')
