"""
Add metrics views and functions migration.

This migration adds views and functions for common metric aggregations and calculations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision = '20240320000001'
down_revision = '20240320000000'  # Points to the previous metrics tables migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add views and functions for metrics."""
    # Create view for rule execution statistics
    op.execute("""
        CREATE OR REPLACE VIEW rule_execution_stats AS
        SELECT 
            rule_id,
            dataset_id,
            COUNT(*) as total_executions,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
            SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_executions,
            AVG(execution_time) as avg_execution_time,
            SUM(violation_count) as total_violations,
            MIN(timestamp) as first_execution,
            MAX(timestamp) as last_execution
        FROM rule_execution_metrics
        GROUP BY rule_id, dataset_id
    """)
    
    # Create view for dataset rule statistics
    op.execute("""
        CREATE OR REPLACE VIEW dataset_rule_stats AS
        SELECT 
            dataset_id,
            COUNT(DISTINCT rule_id) as total_rules,
            COUNT(*) as total_executions,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
            SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_executions,
            AVG(execution_time) as avg_execution_time,
            SUM(violation_count) as total_violations,
            MIN(timestamp) as first_execution,
            MAX(timestamp) as last_execution
        FROM rule_execution_metrics
        GROUP BY dataset_id
    """)
    
    # Create view for rule generation statistics
    op.execute("""
        CREATE OR REPLACE VIEW rule_generation_stats AS
        SELECT 
            dataset_id,
            engine,
            COUNT(*) as total_generations,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_generations,
            SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_generations,
            SUM(rule_count) as total_rules_generated,
            AVG(rule_count) as avg_rules_per_generation,
            MIN(timestamp) as first_generation,
            MAX(timestamp) as last_generation
        FROM rule_generation_metrics
        GROUP BY dataset_id, engine
    """)
    
    # Create function to calculate rule success rate
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_rule_success_rate(
            p_rule_id TEXT,
            p_time_range INTERVAL DEFAULT NULL
        ) RETURNS FLOAT AS $$
        DECLARE
            v_success_rate FLOAT;
        BEGIN
            SELECT 
                CASE 
                    WHEN COUNT(*) = 0 THEN 0
                    ELSE SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*)::FLOAT
                END INTO v_success_rate
            FROM rule_execution_metrics
            WHERE rule_id = p_rule_id
            AND (p_time_range IS NULL OR timestamp >= NOW() - p_time_range);
            
            RETURN v_success_rate;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function to calculate dataset rule success rate
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_dataset_success_rate(
            p_dataset_id TEXT,
            p_time_range INTERVAL DEFAULT NULL
        ) RETURNS FLOAT AS $$
        DECLARE
            v_success_rate FLOAT;
        BEGIN
            SELECT 
                CASE 
                    WHEN COUNT(*) = 0 THEN 0
                    ELSE SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*)::FLOAT
                END INTO v_success_rate
            FROM rule_execution_metrics
            WHERE dataset_id = p_dataset_id
            AND (p_time_range IS NULL OR timestamp >= NOW() - p_time_range);
            
            RETURN v_success_rate;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function to get rule execution trend
    op.execute("""
        CREATE OR REPLACE FUNCTION get_rule_execution_trend(
            p_rule_id TEXT,
            p_time_range INTERVAL DEFAULT '7 days'
        ) RETURNS TABLE (
            date DATE,
            execution_count INTEGER,
            success_count INTEGER,
            violation_count INTEGER,
            avg_execution_time FLOAT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as execution_count,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                SUM(violation_count) as violation_count,
                AVG(execution_time) as avg_execution_time
            FROM rule_execution_metrics
            WHERE rule_id = p_rule_id
            AND timestamp >= NOW() - p_time_range
            GROUP BY DATE(timestamp)
            ORDER BY date;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function to get dataset execution trend
    op.execute("""
        CREATE OR REPLACE FUNCTION get_dataset_execution_trend(
            p_dataset_id TEXT,
            p_time_range INTERVAL DEFAULT '7 days'
        ) RETURNS TABLE (
            date DATE,
            execution_count INTEGER,
            success_count INTEGER,
            violation_count INTEGER,
            avg_execution_time FLOAT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as execution_count,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                SUM(violation_count) as violation_count,
                AVG(execution_time) as avg_execution_time
            FROM rule_execution_metrics
            WHERE dataset_id = p_dataset_id
            AND timestamp >= NOW() - p_time_range
            GROUP BY DATE(timestamp)
            ORDER BY date;
        END;
        $$ LANGUAGE plpgsql;
    """)

def downgrade() -> None:
    """Remove views and functions."""
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS calculate_rule_success_rate(TEXT, INTERVAL)")
    op.execute("DROP FUNCTION IF EXISTS calculate_dataset_success_rate(TEXT, INTERVAL)")
    op.execute("DROP FUNCTION IF EXISTS get_rule_execution_trend(TEXT, INTERVAL)")
    op.execute("DROP FUNCTION IF EXISTS get_dataset_execution_trend(TEXT, INTERVAL)")
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS rule_execution_stats")
    op.execute("DROP VIEW IF EXISTS dataset_rule_stats")
    op.execute("DROP VIEW IF EXISTS rule_generation_stats") 