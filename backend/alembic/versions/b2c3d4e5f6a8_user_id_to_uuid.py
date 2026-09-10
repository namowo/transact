"""convert user.id to uuid

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-08-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column, nullable, old_fk_constraint_name, ondelete)
DEPENDENT_COLUMNS = [
    ("webauthn_challenge", "user_id", False, "webauthn_challenge_user_id_fkey", "CASCADE"),
    ("webauthn_credential", "user_id", False, "webauthn_credential_user_id_fkey", "CASCADE"),
    ("user_token", "user_id", False, "user_token_user_id_fkey", "CASCADE"),
    ("lab_membership_request", "user_id", False, "lab_membership_request_user_id_fkey", "CASCADE"),
    ("lab_membership_request", "reviewed_by_id", True, "lab_membership_request_reviewed_by_id_fkey", "SET NULL"),
    ("study", "quality_checked_by_id", True, "fk_study_quality_checked_by_id_user", "SET NULL"),
]


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.add_column('user', sa.Column('new_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=True))
    op.execute('UPDATE "user" SET new_id = gen_random_uuid() WHERE new_id IS NULL')

    for table, column, _nullable, _fk_name, _ondelete in DEPENDENT_COLUMNS:
        new_column = f'new_{column}'
        op.add_column(table, sa.Column(new_column, postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            f'UPDATE "{table}" t SET {new_column} = u.new_id '
            f'FROM "user" u WHERE t.{column} = u.id'
        )

    op.drop_index(
        'ix_lab_membership_request_one_pending_per_user',
        table_name='lab_membership_request',
        postgresql_where=sa.text("status = 'pending'"),
    )

    for table, column, nullable, fk_name, _ondelete in DEPENDENT_COLUMNS:
        op.drop_constraint(fk_name, table, type_='foreignkey')
        op.drop_column(table, column)
        op.alter_column(table, f'new_{column}', new_column_name=column)
        if not nullable:
            op.alter_column(table, column, nullable=False)

    op.drop_constraint('user_pkey', 'user', type_='primary')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_column('user', 'id')
    op.alter_column('user', 'new_id', new_column_name='id')
    op.alter_column('user', 'id', nullable=False)
    op.create_primary_key('user_pkey', 'user', ['id'])
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)

    for table, column, _nullable, fk_name, ondelete in DEPENDENT_COLUMNS:
        op.create_foreign_key(
            fk_name, table, 'user', [column], ['id'], ondelete=ondelete,
        )

    op.create_index(op.f('ix_webauthn_challenge_user_id'), 'webauthn_challenge', ['user_id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_user_id'), 'webauthn_credential', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_token_user_id'), 'user_token', ['user_id'], unique=False)
    op.create_index(
        'ix_lab_membership_request_one_pending_per_user',
        'lab_membership_request',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    raise NotImplementedError('Downgrade from UUID user ids is not supported.')
