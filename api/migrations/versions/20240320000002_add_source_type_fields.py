"""
Add source type fields migration.

This migration adds fields to support multiple data source types in the datasets table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision = '20240320000002'
down_revision = '20240320000001'  # Points to the previous metrics views migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add source type fields to datasets table."""
    # Add source_type and source_info columns
    op.add_column('datasets', sa.Column('source_type', sa.String(50), nullable=False, server_default='file'))
    op.add_column('datasets', sa.Column('source_info', JSONB, nullable=True))
    
    # Add index on source_type for faster filtering
    op.create_index('ix_datasets_source_type', 'datasets', ['source_type'])

def downgrade() -> None:
    """Remove source type fields from datasets table."""
    op.drop_index('ix_datasets_source_type', table_name='datasets')
    op.drop_column('datasets', 'source_info')
    op.drop_column('datasets', 'source_type') 