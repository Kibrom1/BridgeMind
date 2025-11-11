-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database if not exists (handled by POSTGRES_DB env var)
-- This file runs after database creation

-- Set timezone
SET timezone = 'UTC';

