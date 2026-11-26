"""add study review rounds and comments

Revision ID: d7f9b1c3e5a2
Revises: c4e6a8b0d2f3
Create Date: 2026-11-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd7f9b1c3e5a2'
down_revision: Union[str, None] = 'c4e6a8b0d2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'study',
        sa.Column('review_status', sa.String(), server_default='draft', nullable=False),
    )
    op.execute("UPDATE study SET review_status = 'passed' WHERE quality_check_passed IS TRUE")

    op.create_table(
        'study_review_round',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study.id', ondelete='CASCADE'), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('submitted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision', sa.String(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('snapshot', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.UniqueConstraint('study_id', 'number'),
    )
    op.create_index('ix_study_review_round_study_id', 'study_review_round', ['study_id'])

    op.create_table(
        'study_review_comment',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study_review_comment.id', ondelete='CASCADE'), nullable=True),
        sa.Column('round_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(), server_default='general', nullable=False),
        sa.Column('target_id', sa.String(), nullable=True),
        sa.Column('target_label', sa.String(), nullable=True),
        sa.Column('field_label', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status_changed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_study_review_comment_study_id', 'study_review_comment', ['study_id'])
    op.create_index('ix_study_review_comment_parent_id', 'study_review_comment', ['parent_id'])


def downgrade() -> None:
    op.drop_table('study_review_comment')
    op.drop_table('study_review_round')
    op.drop_column('study', 'review_status')
