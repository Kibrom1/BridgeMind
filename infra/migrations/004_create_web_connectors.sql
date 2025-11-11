-- Migration: Create web connectors table
-- Created: 2024-01-15

CREATE TABLE IF NOT EXISTS web_connectors(
  connector_id SERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  connector_type TEXT CHECK (connector_type IN ('web_search', 'rss_feed', 'webhook', 'browser_automation', 'api_scraper', 'real_time_monitor')) NOT NULL,
  config JSONB NOT NULL, -- type-specific config
  status TEXT CHECK (status IN ('active', 'inactive', 'error')) DEFAULT 'active',
  rate_limit_config JSONB, -- {requests_per_minute: 60, requests_per_hour: 1000}
  cache_config JSONB, -- {ttl_seconds: 3600, cache_key_pattern: "..."}
  auth_config JSONB, -- API keys, tokens, etc. (encrypted)
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  last_accessed_at TIMESTAMPTZ,
  UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_web_connectors_tenant ON web_connectors(tenant_id);
CREATE INDEX IF NOT EXISTS idx_web_connectors_type ON web_connectors(connector_type);
CREATE INDEX IF NOT EXISTS idx_web_connectors_status ON web_connectors(status);

COMMENT ON TABLE web_connectors IS 'Stores web data connector configurations';
COMMENT ON COLUMN web_connectors.config IS 'Type-specific configuration in JSONB format';
COMMENT ON COLUMN web_connectors.auth_config IS 'Encrypted authentication configuration';

