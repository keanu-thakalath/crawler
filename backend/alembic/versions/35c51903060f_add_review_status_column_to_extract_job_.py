"""Add review_status column to extract job result

Revision ID: 35c51903060f
Revises: 2099ce8d5a16
Create Date: 2025-08-29 23:14:39.925706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35c51903060f'
down_revision: Union[str, Sequence[str], None] = '2099ce8d5a16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add review_status column to extract_job_results table."""
    # SQLite doesn't support adding columns with enums directly, so we need to recreate the table
    # Step 1: Create new table with review_status column
    op.create_table('extract_job_results_new',
        sa.Column('job_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('created_at', sa.VARCHAR(length=255), nullable=False),
        sa.Column('summary', sa.TEXT(), nullable=False),
        sa.Column('input_tokens', sa.INTEGER(), nullable=False),
        sa.Column('output_tokens', sa.INTEGER(), nullable=False),
        sa.Column('internal_links', sa.TEXT(), nullable=False),
        sa.Column('external_links', sa.TEXT(), nullable=False),
        sa.Column('file_links', sa.TEXT(), nullable=False),
        sa.Column('review_status', sa.VARCHAR(length=10), nullable=False, server_default='Unreviewed'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ),
        sa.PrimaryKeyConstraint('job_id')
    )
    
    # Step 2: Copy data from old table to new table (with default review_status)
    op.execute("INSERT INTO extract_job_results_new (job_id, created_at, summary, input_tokens, output_tokens, internal_links, external_links, file_links, review_status) SELECT job_id, created_at, summary, input_tokens, output_tokens, internal_links, external_links, file_links, 'Unreviewed' FROM extract_job_results")
    
    # Step 3: Drop old table
    op.drop_table('extract_job_results')
    
    # Step 4: Rename new table to original name
    op.execute('ALTER TABLE extract_job_results_new RENAME TO extract_job_results')


def downgrade() -> None:
    """Remove review_status column from extract_job_results table."""
    # Recreate table without review_status column
    op.create_table('extract_job_results_new',
        sa.Column('job_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('created_at', sa.VARCHAR(length=255), nullable=False),
        sa.Column('summary', sa.TEXT(), nullable=False),
        sa.Column('input_tokens', sa.INTEGER(), nullable=False),
        sa.Column('output_tokens', sa.INTEGER(), nullable=False),
        sa.Column('internal_links', sa.TEXT(), nullable=False),
        sa.Column('external_links', sa.TEXT(), nullable=False),
        sa.Column('file_links', sa.TEXT(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ),
        sa.PrimaryKeyConstraint('job_id')
    )
    
    # Copy data back (excluding review_status)
    op.execute("INSERT INTO extract_job_results_new (job_id, created_at, summary, input_tokens, output_tokens, internal_links, external_links, file_links) SELECT job_id, created_at, summary, input_tokens, output_tokens, internal_links, external_links, file_links FROM extract_job_results")
    
    # Drop old table and rename
    op.drop_table('extract_job_results')
    op.execute('ALTER TABLE extract_job_results_new RENAME TO extract_job_results')