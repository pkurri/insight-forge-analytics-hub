-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id),
    source_type VARCHAR(50) NOT NULL, -- 'upload', 'api', 'database'
    file_path TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ds_metadata JSONB DEFAULT '{}'::jsonb,
    cleaned_file_path TEXT,
    processed_file_path TEXT,
    last_cleaned_at TIMESTAMP WITH TIME ZONE,
    last_processed_at TIMESTAMP WITH TIME ZONE
);

-- Create dataset_columns table
CREATE TABLE IF NOT EXISTS dataset_columns (
    id SERIAL PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    nullable BOOLEAN DEFAULT true,
    stats JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create vector_embeddings table
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    text_content TEXT NOT NULL,
    embedding vector(768) NOT NULL, -- 768-dimensional embeddings
    vector_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    messages JSONB DEFAULT '[]'::jsonb
);

-- Create pipeline_runs table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    pipeline_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create api_connections table
CREATE TABLE IF NOT EXISTS api_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    api_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP WITH TIME ZONE
);

-- Create database_connections table
CREATE TABLE IF NOT EXISTS database_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    db_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_datasets_user_id ON datasets(user_id);
CREATE INDEX idx_datasets_status ON datasets(status);
CREATE INDEX idx_vector_embeddings_dataset_id ON vector_embeddings(dataset_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_pipeline_runs_dataset_id ON pipeline_runs(dataset_id);
CREATE INDEX idx_api_connections_user_id ON api_connections(user_id);
CREATE INDEX idx_database_connections_user_id ON database_connections(user_id);

-- Create vector similarity index
CREATE INDEX vector_embeddings_embedding_idx ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create business_rules table
CREATE TABLE IF NOT EXISTS business_rules (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL, -- 'manual', 'ai_generated', 'imported'
    source VARCHAR(50), -- 'great_expectations', 'pydantic', 'huffman'
    condition TEXT NOT NULL,
    action TEXT,
    rules_metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    priority INTEGER DEFAULT 0
);

-- Create rule_execution_logs table
CREATE TABLE IF NOT EXISTS rule_execution_logs (
    id SERIAL PRIMARY KEY,
    rule_id UUID REFERENCES business_rules(id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    affected_rows INTEGER,
    error_message TEXT,
    execution_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for business rules
CREATE INDEX idx_business_rules_dataset_id ON business_rules(dataset_id);
CREATE INDEX idx_business_rules_type ON business_rules(rule_type);
CREATE INDEX idx_rule_execution_logs_rule_id ON rule_execution_logs(rule_id);
CREATE INDEX idx_rule_execution_logs_dataset_id ON rule_execution_logs(dataset_id);
