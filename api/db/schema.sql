-- Database Schema for DataForge Analytics

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Create datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_info JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dataset columns table
CREATE TABLE IF NOT EXISTS dataset_columns (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,  -- string, number, boolean, date, etc.
    nullable BOOLEAN DEFAULT TRUE,
    stats JSONB DEFAULT '{}'::jsonb,  -- min, max, mean, unique count, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Business rules table
CREATE TABLE IF NOT EXISTS business_rules (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    condition TEXT NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium',  -- low, medium, high
    message TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    model_generated BOOLEAN DEFAULT FALSE,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create pipeline_runs table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    pipeline_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create pipeline_steps table
CREATE TABLE IF NOT EXISTS pipeline_steps (
    id SERIAL PRIMARY KEY,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    step_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    pipeline_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Vector embeddings table
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    record_id VARCHAR(255) NOT NULL,
    embedding vector(1536),  -- Dimension must match VECTOR_DIMENSION in backend config
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by dataset
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_dataset_id ON vector_embeddings(dataset_id);

-- Vector similarity index (requires pgvector extension)
CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- Anomaly detection results
CREATE TABLE IF NOT EXISTS anomaly_detection (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    record_id VARCHAR(255) NOT NULL,
    anomaly_score FLOAT NOT NULL,
    anomaly_type VARCHAR(100),  -- outlier, drift, novelty, etc.
    algorithm_used VARCHAR(100) NOT NULL,
    detection_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB DEFAULT '{}'::jsonb
);

-- External API connections
CREATE TABLE IF NOT EXISTS external_apis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL,
    auth_type VARCHAR(50) NOT NULL,  -- basic, bearer, api_key, none
    auth_credentials JSONB DEFAULT '{}'::jsonb,
    headers JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Database connections
CREATE TABLE IF NOT EXISTS db_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    connection_type VARCHAR(50) NOT NULL,  -- postgresql, mysql, sqlserver, etc.
    connection_string VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
CREATE INDEX IF NOT EXISTS idx_dataset_columns_dataset_id ON dataset_columns(dataset_id);
CREATE INDEX IF NOT EXISTS idx_business_rules_dataset_id ON business_rules(dataset_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_dataset_id ON pipeline_runs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_pipeline_run_id ON pipeline_steps(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_status ON pipeline_steps(status);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_dataset_id ON vector_embeddings(dataset_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_detection_dataset_id ON anomaly_detection(dataset_id);

-- Create vector index for efficient similarity search
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_embedding ON vector_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_datasets_updated_at
    BEFORE UPDATE ON datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_runs_updated_at
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_steps_updated_at
    BEFORE UPDATE ON pipeline_steps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
