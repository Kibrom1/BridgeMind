-- Migration: Create database connectors table
-- Created: 2024-01-15

CREATE TABLE IF NOT EXISTS db_connectors(
  connector_id SERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  db_type TEXT CHECK (db_type IN ('postgresql', 'mysql', 'sqlite', 'mssql', 'snowflake', 'bigquery')) NOT NULL,
  connection_string TEXT NOT NULL, -- encrypted
  schema_info JSONB, -- cached schema: {tables: [{name, columns: [...]}]}
  status TEXT CHECK (status IN ('active', 'inactive', 'error')) DEFAULT 'active',
  read_only BOOLEAN DEFAULT true,
  max_rows_per_query INT DEFAULT 100,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  last_schema_sync TIMESTAMPTZ,
  UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_db_connectors_tenant ON db_connectors(tenant_id);
CREATE INDEX IF NOT EXISTS idx_db_connectors_status ON db_connectors(status);
CREATE INDEX IF NOT EXISTS idx_db_connectors_db_type ON db_connectors(db_type);

COMMENT ON TABLE db_connectors IS 'Stores database connector configurations';
COMMENT ON COLUMN db_connectors.connection_string IS 'Encrypted database connection string';
COMMENT ON COLUMN db_connectors.schema_info IS 'Cached database schema information in JSONB format';

