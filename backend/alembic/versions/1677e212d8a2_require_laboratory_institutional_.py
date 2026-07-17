"""require laboratory institutional_affiliation, city and country

Revision ID: 1677e212d8a2
Revises: c09977495acd
Create Date: 2026-07-17 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1677e212d8a2'
down_revision: Union[str, None] = 'c09977495acd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE laboratory SET country = 'Unknown' WHERE country IS NULL")
    op.execute("UPDATE laboratory SET city = 'Unknown' WHERE city IS NULL")
    op.execute(
        "UPDATE laboratory SET institutional_affiliation = 'Unknown' "
        "WHERE institutional_affiliation IS NULL"
    )
    op.alter_column('laboratory', 'country',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('laboratory', 'city',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('laboratory', 'institutional_affiliation',
               existing_type=sa.VARCHAR(),
               nullable=False)


def downgrade() -> None:
    op.alter_column('laboratory', 'institutional_affiliation',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('laboratory', 'city',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('laboratory', 'country',
               existing_type=sa.VARCHAR(),
               nullable=True)
