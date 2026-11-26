"""add privacy policy versions and consents

The privacy policy moves from site_settings into versioned, immutable
records. An existing policy becomes the published version 1. No consents
are recorded for it - they were never stored - so existing users are asked
to agree to it on their next sign-in.

Revision ID: c4e6a8b0d2f3
Revises: b3d5f7a9c1e2
Create Date: 2026-11-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4e6a8b0d2f3'
down_revision: Union[str, None] = 'b3d5f7a9c1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'privacy_policy_version',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('mode', sa.String(), server_default='text', nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['published_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
    )
    op.create_index(op.f('ix_privacy_policy_version_id'), 'privacy_policy_version', ['id'], unique=False)
    op.create_index(
        op.f('ix_privacy_policy_version_published_at'),
        'privacy_policy_version',
        ['published_at'],
        unique=False,
    )
    op.create_index(
        'uq_privacy_policy_version_single_draft',
        'privacy_policy_version',
        [sa.text('(published_at IS NULL)')],
        unique=True,
        postgresql_where=sa.text('published_at IS NULL'),
    )

    op.create_table(
        'privacy_policy_consent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_version_id', sa.Integer(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['policy_version_id'], ['privacy_policy_version.id'], ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'policy_version_id'),
    )
    op.create_index(op.f('ix_privacy_policy_consent_user_id'), 'privacy_policy_consent', ['user_id'], unique=False)
    op.create_index(
        op.f('ix_privacy_policy_consent_policy_version_id'),
        'privacy_policy_consent',
        ['policy_version_id'],
        unique=False,
    )

    # The existing policy, if one was set up, becomes version 1.
    op.execute(
        """
        INSERT INTO privacy_policy_version (version, mode, text, url, published_at)
        SELECT 1, privacy_policy_mode, privacy_policy_text, privacy_policy_url, now()
        FROM site_settings
        WHERE id = 1
          AND (
            (privacy_policy_mode = 'text' AND coalesce(trim(privacy_policy_text), '') <> '')
            OR (privacy_policy_mode = 'url' AND coalesce(trim(privacy_policy_url), '') <> '')
          )
        """
    )

    op.drop_column('site_settings', 'privacy_policy_url')
    op.drop_column('site_settings', 'privacy_policy_text')
    op.drop_column('site_settings', 'privacy_policy_mode')


def downgrade() -> None:
    op.add_column(
        'site_settings',
        sa.Column('privacy_policy_mode', sa.String(), server_default='text', nullable=False),
    )
    op.add_column('site_settings', sa.Column('privacy_policy_text', sa.String(), nullable=True))
    op.add_column('site_settings', sa.Column('privacy_policy_url', sa.String(), nullable=True))
    # Keep the active policy; the history and consents are lost.
    op.execute(
        """
        UPDATE site_settings SET
            privacy_policy_mode = p.mode,
            privacy_policy_text = p.text,
            privacy_policy_url = p.url
        FROM (
            SELECT mode, text, url FROM privacy_policy_version
            WHERE version IS NOT NULL ORDER BY version DESC LIMIT 1
        ) AS p
        WHERE site_settings.id = 1
        """
    )

    op.drop_index(op.f('ix_privacy_policy_consent_policy_version_id'), table_name='privacy_policy_consent')
    op.drop_index(op.f('ix_privacy_policy_consent_user_id'), table_name='privacy_policy_consent')
    op.drop_table('privacy_policy_consent')
    op.drop_index('uq_privacy_policy_version_single_draft', table_name='privacy_policy_version')
    op.drop_index(op.f('ix_privacy_policy_version_published_at'), table_name='privacy_policy_version')
    op.drop_index(op.f('ix_privacy_policy_version_id'), table_name='privacy_policy_version')
    op.drop_table('privacy_policy_version')
