-- Migration: Create API connectors table
-- Created: 2024-01-15

CREATE TABLE IF NOT EXISTS api_connectors(
  connector_id SERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  base_url TEXT NOT NULL,
  openapi_spec JSONB NOT NULL,
  auth_type TEXT CHECK (auth_type IN ('none', 'api_key', 'bearer', 'basic', 'oauth2')),
  auth_config JSONB, -- encrypted secrets: {header_name, api_key}, {token}, etc.
  status TEXT CHECK (status IN ('active', 'inactive', 'error')) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_api_connectors_tenant ON api_connectors(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_connectors_status ON api_connectors(status);

COMMENT ON TABLE api_connectors IS 'Stores OpenAPI connector configurations';
COMMENT ON COLUMN api_connectors.openapi_spec IS 'Full OpenAPI specification in JSONB format';
COMMENT ON COLUMN api_connectors.auth_config IS 'Encrypted authentication configuration';

