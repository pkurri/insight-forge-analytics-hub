-- Migration for Conversation, Message, Evaluation tables
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    metadata JSON DEFAULT '{}'
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    sender VARCHAR NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP
);

CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    feedback TEXT,
    rating INTEGER,
    category VARCHAR,
    created_at TIMESTAMP
);
