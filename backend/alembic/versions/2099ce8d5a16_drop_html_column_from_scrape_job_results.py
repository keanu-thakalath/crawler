"""Drop html column from scrape_job_results

Revision ID: 2099ce8d5a16
Revises: fcd4b1791743
Create Date: 2025-08-29 23:01:10.707873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2099ce8d5a16'
down_revision: Union[str, Sequence[str], None] = 'fcd4b1791743'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop html column from scrape_job_results table."""
    # SQLite doesn't support dropping columns directly, so we need to recreate the table
    # Step 1: Create new table without html column
    op.create_table('scrape_job_results_new',
        sa.Column('job_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('created_at', sa.VARCHAR(length=255), nullable=False),
        sa.Column('markdown', sa.TEXT(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ),
        sa.PrimaryKeyConstraint('job_id')
    )
    
    # Step 2: Copy data from old table to new table (excluding html column)
    op.execute('INSERT INTO scrape_job_results_new (job_id, created_at, markdown) SELECT job_id, created_at, markdown FROM scrape_job_results')
    
    # Step 3: Drop old table
    op.drop_table('scrape_job_results')
    
    # Step 4: Rename new table to original name
    op.execute('ALTER TABLE scrape_job_results_new RENAME TO scrape_job_results')


def downgrade() -> None:
    """Add html column back to scrape_job_results table."""
    # Recreate table with html column
    op.create_table('scrape_job_results_new',
        sa.Column('job_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('created_at', sa.VARCHAR(length=255), nullable=False),
        sa.Column('markdown', sa.TEXT(), nullable=False),
        sa.Column('html', sa.TEXT(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ),
        sa.PrimaryKeyConstraint('job_id')
    )
    
    # Copy data back (html will be empty)
    op.execute("INSERT INTO scrape_job_results_new (job_id, created_at, markdown, html) SELECT job_id, created_at, markdown, '' FROM scrape_job_results")
    
    # Drop old table and rename
    op.drop_table('scrape_job_results')
    op.execute('ALTER TABLE scrape_job_results_new RENAME TO scrape_job_results')