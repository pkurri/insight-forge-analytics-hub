"""
Create metrics tables migration.

This migration creates the tables needed for storing business rule metrics.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision = '20240320000000'
down_revision = None  # Update this to the previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create metrics tables."""
    # Create rule execution metrics table
    op.create_table(
        'rule_execution_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('dataset_id', sa.String(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('violation_count', sa.Integer(), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meta', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['rule_id'],
            ['business_rules.id'],
            ondelete='CASCADE',
            name='fk_rule_execution_metrics_rule_id'
        ),
        sa.ForeignKeyConstraint(
            ['dataset_id'],
            ['datasets.id'],
            ondelete='CASCADE',
            name='fk_rule_execution_metrics_dataset_id'
        ),
        sa.CheckConstraint(
            'violation_count >= 0',
            name='chk_rule_execution_metrics_violation_count'
        ),
        sa.CheckConstraint(
            'execution_time >= 0',
            name='chk_rule_execution_metrics_execution_time'
        )
    )
    
    # Create indexes
    op.create_index(
        'ix_rule_execution_metrics_rule_id',
        'rule_execution_metrics',
        ['rule_id']
    )
    op.create_index(
        'ix_rule_execution_metrics_dataset_id',
        'rule_execution_metrics',
        ['dataset_id']
    )
    op.create_index(
        'ix_rule_execution_metrics_timestamp',
        'rule_execution_metrics',
        ['timestamp']
    )
    op.create_index(
        'ix_rule_execution_metrics_success',
        'rule_execution_metrics',
        ['success']
    )
    op.create_index(
        'ix_rule_execution_metrics_rule_dataset',
        'rule_execution_metrics',
        ['rule_id', 'dataset_id']
    )
    
    # Create rule generation metrics table
    op.create_table(
        'rule_generation_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.String(), nullable=False),
        sa.Column('engine', sa.String(), nullable=False),
        sa.Column('rule_count', sa.Integer(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meta', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['dataset_id'],
            ['datasets.id'],
            ondelete='CASCADE',
            name='fk_rule_generation_metrics_dataset_id'
        ),
        sa.CheckConstraint(
            'rule_count >= 0',
            name='chk_rule_generation_metrics_rule_count'
        )
    )
    
    # Create indexes
    op.create_index(
        'ix_rule_generation_metrics_dataset_id',
        'rule_generation_metrics',
        ['dataset_id']
    )
    op.create_index(
        'ix_rule_generation_metrics_timestamp',
        'rule_generation_metrics',
        ['timestamp']
    )
    op.create_index(
        'ix_rule_generation_metrics_engine',
        'rule_generation_metrics',
        ['engine']
    )
    op.create_index(
        'ix_rule_generation_metrics_success',
        'rule_generation_metrics',
        ['success']
    )
    op.create_index(
        'ix_rule_generation_metrics_dataset_engine',
        'rule_generation_metrics',
        ['dataset_id', 'engine']
    )

def downgrade() -> None:
    """Drop metrics tables."""
    op.drop_table('rule_generation_metrics')
    op.drop_table('rule_execution_metrics') 