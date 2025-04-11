
-- Analytics and Business Rules Schema

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Data Profiles Table to store dataset profiling results
CREATE TABLE IF NOT EXISTS data_profiles (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL,
    profile_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    summary JSONB NOT NULL,
    detailed_profile JSONB,
    CONSTRAINT fk_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

-- Anomaly Detection Results
CREATE TABLE IF NOT EXISTS anomaly_detections (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL,
    detection_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    detection_method VARCHAR(50) NOT NULL,
    anomaly_count INTEGER NOT NULL,
    anomaly_types JSONB,
    detected_anomalies JSONB,
    method_specific_params JSONB,
    CONSTRAINT fk_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

-- Business Rules Table 
CREATE TABLE IF NOT EXISTS business_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dataset_id INTEGER NOT NULL,
    condition TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    message TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    model_generated BOOLEAN DEFAULT FALSE,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high'))
);

-- Business Rule Validations
CREATE TABLE IF NOT EXISTS rule_validations (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    dataset_id INTEGER NOT NULL,
    validation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    violations_count INTEGER NOT NULL,
    violations JSONB,
    CONSTRAINT fk_rule FOREIGN KEY (rule_id) REFERENCES business_rules(id) ON DELETE CASCADE,
    CONSTRAINT fk_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

-- Monitoring Metrics and Alerts
CREATE TABLE IF NOT EXISTS monitoring_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a hypertable for time-series metrics
SELECT create_hypertable('monitoring_metrics', 'recorded_at', if_not_exists => TRUE);

-- Monitoring Alerts
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id SERIAL PRIMARY KEY,
    alert_name VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'acknowledged', 'resolved'))
);

-- Vector Embeddings for datasets
CREATE TABLE IF NOT EXISTS dataset_embeddings (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

-- Create index on embeddings for similarity search
CREATE INDEX IF NOT EXISTS dataset_embeddings_idx ON dataset_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- System Configuration table for dynamic settings
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Audit logs for tracking changes to the system
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100),
    user_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Insert default system configurations
INSERT INTO system_config (key, value, description)
VALUES 
('anomaly_detection.default_method', '{"method": "isolation_forest", "params": {"contamination": 0.05}}', 'Default method for anomaly detection'),
('vector_embeddings.model', '{"name": "text-embedding-3-small", "dimension": 1536}', 'Default embedding model configuration'),
('monitoring.alert_thresholds', '{"cpu_usage": 80, "memory_usage": 85, "api_latency_ms": 500}', 'Default monitoring alert thresholds')
ON CONFLICT (key) DO NOTHING;
