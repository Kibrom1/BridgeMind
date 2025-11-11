-- Migration: Create document sources and chunks tables
-- Created: 2024-01-15

CREATE TABLE IF NOT EXISTS document_sources(
  source_id SERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  source_type TEXT CHECK (source_type IN ('local_fs', 's3', 'gcs', 'azure_blob', 'web_scrape', 'api', 'sharepoint', 'confluence', 'notion')) NOT NULL,
  config JSONB NOT NULL, -- source-specific config: {path, bucket, url_pattern, auth, etc.}
  file_filters JSONB, -- {allowed_extensions: ['.pdf', '.md'], max_file_size_mb: 50, exclude_patterns: ['*.tmp']}
  status TEXT CHECK (status IN ('active', 'inactive', 'error', 'syncing')) DEFAULT 'active',
  auto_sync BOOLEAN DEFAULT false,
  sync_schedule TEXT, -- cron expression for periodic sync
  last_sync_at TIMESTAMPTZ,
  files_count INT DEFAULT 0,
  total_size_bytes BIGINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_document_sources_tenant ON document_sources(tenant_id);
CREATE INDEX IF NOT EXISTS idx_document_sources_status ON document_sources(status);
CREATE INDEX IF NOT EXISTS idx_document_sources_source_type ON document_sources(source_type);

-- Document chunks table for RAG
CREATE TABLE IF NOT EXISTS document_chunks(
  chunk_id SERIAL PRIMARY KEY,
  source_id INT REFERENCES document_sources(source_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_format TEXT NOT NULL,
  file_size_bytes INT,
  chunk_index INT NOT NULL,
  chunk_text TEXT NOT NULL,
  embedding VECTOR(1536), -- OpenAI ada-002 or similar
  metadata JSONB, -- {page, lineStart, lineEnd, section, headings[], title}
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(source_id, file_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_tenant ON document_chunks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_source ON document_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_file_path ON document_chunks(file_path);
-- Vector similarity search index (created after pgvector extension is enabled)
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE document_sources IS 'Stores document source connector configurations';
COMMENT ON TABLE document_chunks IS 'Stores document chunks with embeddings for RAG';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding for semantic search (1536 dimensions for OpenAI ada-002)';

