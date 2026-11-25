"""user groups and permissions

Replaces the user flags is_superuser, can_manage_lab_users and
can_quality_check with groups bundling permissions (see
app.core.permission_catalog):

- creates the built-in Administrator, Lab administrator and Quality checker
  groups and moves every flagged user into the matching group,
- adds laboratory.allow_admin_data_entry (on by default), with which a
  laboratory decides whether platform admins may work on its data.

Downgrading restores the flags from the built-in group memberships; custom
groups are lost.

Revision ID: d7f9b1c3e5a7
Revises: c5e7a9b1d3f4
Create Date: 2026-11-25 12:00:00.000000

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd7f9b1c3e5a7'
down_revision: Union[str, None] = 'c5e7a9b1d3f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Frozen copy of the defaults at the time of this migration - later changes
# to app.core.permission_catalog must not change what this migration does.
ALL = [
    "catalog.delete",
    "catalog.edit",
    "data.enter",
    "groups.manage",
    "lab.manage_groups",
    "lab.manage_members",
    "lab.manage_settings",
    "laboratories.edit_all_data",
    "laboratories.manage",
    "methods.manage",
    "site_settings.manage",
    "studies.quality_check",
    "studies.view_all",
    "users.manage",
]
SYSTEM_GROUPS = [
    # key, name, description, permissions, the user flag it replaces
    ("administrator", "Administrator", "Runs the platform.", ALL, "is_superuser"),
    (
        "lab_administrator",
        "Lab administrator",
        "Manages the members and settings of their own laboratory.",
        ["catalog.edit", "lab.manage_groups", "lab.manage_members", "lab.manage_settings"],
        "can_manage_lab_users",
    ),
    (
        "quality_checker",
        "Quality checker",
        "Reviews studies before publication.",
        ["studies.quality_check"],
        "can_quality_check",
    ),
]


def upgrade() -> None:
    op.create_table(
        'user_group',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('system_key', sa.String(length=50), nullable=True),
        sa.Column('laboratory_id', sa.UUID(), nullable=True),
        sa.Column(
            'permissions',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['laboratory_id'], ['laboratory.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system_key'),
    )
    op.create_index(op.f('ix_user_group_id'), 'user_group', ['id'], unique=False)
    op.create_index(
        op.f('ix_user_group_laboratory_id'), 'user_group', ['laboratory_id'], unique=False
    )

    op.create_table(
        'user_group_member',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['user_group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'group_id'),
    )
    op.create_index(
        op.f('ix_user_group_member_group_id'), 'user_group_member', ['group_id'], unique=False
    )

    bind = op.get_bind()
    for key, name, description, permissions, flag in SYSTEM_GROUPS:
        bind.execute(
            sa.text(
                """
                INSERT INTO user_group (name, description, system_key, permissions)
                VALUES (:name, :description, :key, CAST(:permissions AS jsonb))
                """
            ),
            {
                "name": name,
                "description": description,
                "key": key,
                "permissions": json.dumps(sorted(permissions)),
            },
        )
        bind.execute(
            sa.text(
                f"""
                INSERT INTO user_group_member (user_id, group_id)
                SELECT "user".id, user_group.id
                FROM "user", user_group
                WHERE "user".{flag} AND user_group.system_key = :key
                """
            ),
            {"key": key},
        )

    op.drop_column('user', 'is_superuser')
    op.drop_column('user', 'can_manage_lab_users')
    op.drop_column('user', 'can_quality_check')

    op.add_column(
        'laboratory',
        sa.Column(
            'allow_admin_data_entry',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('laboratory', 'allow_admin_data_entry')

    for _key, _name, _description, _permissions, flag in SYSTEM_GROUPS:
        op.add_column(
            'user',
            sa.Column(flag, sa.Boolean(), server_default=sa.text('false'), nullable=False),
        )
    bind = op.get_bind()
    for key, _name, _description, _permissions, flag in SYSTEM_GROUPS:
        bind.execute(
            sa.text(
                f"""
                UPDATE "user" SET {flag} = true
                FROM user_group_member
                JOIN user_group ON user_group.id = user_group_member.group_id
                WHERE user_group_member.user_id = "user".id
                  AND user_group.system_key = :key
                """
            ),
            {"key": key},
        )

    op.drop_index(op.f('ix_user_group_member_group_id'), table_name='user_group_member')
    op.drop_table('user_group_member')
    op.drop_index(op.f('ix_user_group_laboratory_id'), table_name='user_group')
    op.drop_index(op.f('ix_user_group_id'), table_name='user_group')
    op.drop_table('user_group')
