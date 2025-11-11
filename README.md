# BridgeMind – Pre-Coding Requirements Document

## Overview

BridgeMind is an AI agent that unifies structured and unstructured data sources—including APIs, documentation, and databases—into a single intelligent query interface. This document defines the **detailed requirements** to scaffold BridgeMind for development, including one of each data source type: a database, OpenAPI specification, document, wiki page, CSV, and other formats.

---

## 1. Goals and Scope

### Objective

Build an MVP that can:

* Ingest and index multiple data types.
* Answer questions with **citations** from source material.
* Use **tools** to execute SQL and API calls safely.
* Support **multi-tenant** and **auditable** architecture.

### Primary Use Cases

1. **Knowledge Q&A:** Natural language questions answered with citations.
2. **Data Querying:** Translate natural language to SQL, execute, and return data.
3. **API Interaction:** Read OpenAPI specs, generate requests, and safely execute.
4. **Documentation Search:** Retrieve and cite results from uploaded files.
5. **Dynamic API Integration:** Add new OpenAPI connectors that become available as tools for the LLM agent.
6. **Multi-Database Analytics:** Connect to multiple databases and query across them with proper SQL dialect generation.
7. **Multi-Source Document Management:** Connect to multiple document sources (folders, S3, wikis) and search across them with source attribution.
8. **Real-Time Web Data Access:** Access live web data via search APIs, RSS feeds, webhooks, and browser automation for current information.

---

## 2. Tech Stack

| Layer          | Technology                               |
| -------------- | ---------------------------------------- |
| Backend        | Python (FastAPI)    |
| LLM Agent      | OpenAI/Anthropic (tool-calling mode)     |
| Database       | PostgreSQL 15 (pgvector enabled)         |
| Object Storage | Local FS (dev) / S3-compatible interface |
| Frontend       | React                             |
| Observability  | OpenTelemetry (logs + traces)            |
| Auth           | Dev token (MVP), OIDC later              |

---

## 3. Directory Structure

```
bridgemind/
  api/
    main.py / index.ts
    routes/
      chat.py
      tools_sql.py
      tools_api.py
      admin_connectors.py
    services/
      orchestrator.py
      retrieval.py
      sql_agent.py
      db_connector_manager.py
      api_agent.py
      api_connector_manager.py
      file_agent.py
      document_source_manager.py
      web_connector_manager.py
      web_agent.py
  ui/
    src/App.tsx
  data_samples/
    db/seed.sql
    openapi/petstore.yaml
    docs/
      handbook.pdf
      wiki_page.md
      pricing.csv
      faq.docx
      release_notes.html
      readme.txt
      product.json
      inventory.xlsx
  infra/
    docker-compose.yml
    init_db.sql
    migrations/
     001_create_api_connectors.sql
     002_create_db_connectors.sql
     003_create_document_sources.sql
     004_create_web_connectors.sql
  tests/
    e2e/
    unit/
```

---

## 4. Data Connectors

### 4.1 Database Connectors

**Purpose:** SQL agent for analytics across multiple databases. Support for PostgreSQL, MySQL, SQLite, and other SQL databases.

**Sample Database Schema (for initial seed data):**

```sql
CREATE TABLE customers(
  customer_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  country TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE orders(
  order_id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(customer_id),
  order_date DATE NOT NULL,
  status TEXT CHECK (status IN ('pending','shipped','refunded')),
  total_amount NUMERIC(10,2) NOT NULL
);

CREATE TABLE refunds(
  refund_id SERIAL PRIMARY KEY,
  order_id INT REFERENCES orders(order_id),
  reason TEXT,
  refund_date DATE NOT NULL,
  amount NUMERIC(10,2) NOT NULL
);
```

**Sample Seed:** 25 customers, 120 orders, 12 refunds.

**Database Connector Storage Schema:**

```sql
CREATE TABLE db_connectors(
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

CREATE INDEX idx_db_connectors_tenant ON db_connectors(tenant_id);
```

**Connector Management Features:**

* **Add Connector:** Register new database connections (PostgreSQL, MySQL, SQLite, etc.)
* **Multiple Databases:** Support multiple active database connectors per tenant
* **Schema Discovery:** Automatically discover and cache database schemas (tables, columns, types)
* **Schema Sync:** Periodic refresh of schema information
* **Query Routing:** Route SQL queries to correct database based on table/connector mapping
* **Database-Specific SQL:** Generate database-appropriate SQL dialects
* **Connection Pooling:** Manage connection pools per connector
* **Status Management:** Enable/disable connectors without deletion

**SQL Agent Requirements:**

* Read-only queries by default; limit 100 rows; return SQL + provenance.
* Support multiple database connectors simultaneously.
* Auto-detect database type and generate appropriate SQL dialect.
* Schema-aware query generation (knows available tables/columns per database).
* Query routing: identify target database from table names or explicit connector selection.
* Connection string encryption at rest.
* Schema caching with TTL for performance.

---

### 4.2 OpenAPI Specification

**Purpose:** Dynamic API connector management - users can add multiple OpenAPI specifications that become available as tools for the LLM agent.

**Sample File:** `petstore.yaml` (OpenAPI 3.0)

**Sample Endpoints:**

* `GET /pets?limit={n}`
* `POST /pets`
* `GET /pets/{id}`
* `POST /appointments`

**Connector Storage Schema:**

```sql
CREATE TABLE api_connectors(
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

CREATE INDEX idx_api_connectors_tenant ON api_connectors(tenant_id);
```

**Connector Management Features:**

* **Add Connector:** Upload OpenAPI spec (YAML/JSON) via file or URL
* **Multiple Connectors:** Support multiple active OpenAPI connectors per tenant
* **Tool Registration:** Automatically convert OpenAPI endpoints to LLM function tools
* **Dynamic Tool Discovery:** LLM agent can discover and use tools from all active connectors
* **Connector Metadata:** Store name, description, base URL, auth config per connector
* **Status Management:** Enable/disable connectors without deletion

**API Agent Requirements:**

* Validate params against schema.
* Default to **preview mode** (show curl + JSON).
* Mask secrets in logs.
* Support multiple API connectors simultaneously.
* Tool naming: `{connector_name}_{operation_id}` to avoid conflicts.
* Route requests to correct base URL based on connector.

---

### 4.3 Document Source Connectors

**Purpose:** Manage multiple unstructured data sources (document repositories, folders, S3 buckets, wikis, etc.) with support for various file formats.

**Supported File Formats:**

| Format   | Extensions          | Purpose                           |
| -------- | ------------------ | --------------------------------- |
| PDF      | `.pdf`             | Policy documents, reports        |
| Markdown | `.md`, `.markdown` | Wiki pages, documentation         |
| CSV      | `.csv`             | Tabular data                      |
| DOCX     | `.docx`            | Word documents, FAQs              |
| HTML     | `.html`, `.htm`    | Web pages, release notes          |
| TXT      | `.txt`             | Plain text files                  |
| JSON     | `.json`            | Structured data                   |
| XLSX     | `.xlsx`, `.xls`    | Excel spreadsheets                |
| RTF      | `.rtf`             | Rich text format                  |
| PPTX     | `.pptx`, `.ppt`    | PowerPoint presentations          |

**Document Source Connector Storage Schema:**

```sql
CREATE TABLE document_sources(
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

CREATE INDEX idx_document_sources_tenant ON document_sources(tenant_id);
CREATE INDEX idx_document_sources_status ON document_sources(status);

-- Document chunks table for RAG
CREATE TABLE document_chunks(
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

CREATE INDEX idx_document_chunks_tenant ON document_chunks(tenant_id);
CREATE INDEX idx_document_chunks_source ON document_chunks(source_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

**Connector Management Features:**

* **Add Source:** Register new document sources (local folders, S3 buckets, web URLs, etc.)
* **Multiple Sources:** Support multiple active document sources per tenant
* **Source Organization:** Group files by source (e.g., "Company Wiki", "Product Docs", "Support KB")
* **Auto-Sync:** Periodic synchronization of document sources
* **File Filtering:** Configure allowed file types, size limits, exclude patterns
* **Incremental Sync:** Only process new/changed files
* **Source Metadata:** Track file counts, total size, last sync time
* **Status Management:** Enable/disable sources without deletion

**File Agent Requirements:**

* Chunk text 700–1,000 tokens with headings preserved.
* Extract and preserve page/line info (PDF, DOCX).
* Store original file + embeddings in vector database.
* Return citations with source attribution: `(Company Wiki: handbook.pdf p.4, lines 120–137)`.
* Support multiple document sources simultaneously.
* Source-aware retrieval (can filter/search within specific source).
* Handle various file formats with appropriate parsers.
* Extract metadata (title, author, creation date) when available.
* Support nested folder structures and maintain path information.

---

### 4.4 Web Data Connectors

**Purpose:** Access real-time data from the web including web search, RSS feeds, webhooks, and dynamic web content. This goes beyond document scraping to enable live web data retrieval.

**Web Data Connector Storage Schema:**

```sql
CREATE TABLE web_connectors(
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

CREATE INDEX idx_web_connectors_tenant ON web_connectors(tenant_id);
CREATE INDEX idx_web_connectors_type ON web_connectors(connector_type);
```

**Connector Types and Use Cases:**

1. **Web Search (`web_search`):**
   * Integrate with search APIs (Google, Bing, DuckDuckGo, SerpAPI)
   * Real-time web search results for current information
   * Use case: "What's the latest news about X?", "Find recent articles about Y"

2. **RSS Feeds (`rss_feed`):**
   * Subscribe to RSS/Atom feeds
   * Periodic polling for new content
   * Use case: News feeds, blog updates, product releases

3. **Webhooks (`webhook`):**
   * Receive real-time data via webhooks
   * Store webhook payloads for querying
   * Use case: GitHub events, Slack messages, external system notifications

4. **Browser Automation (`browser_automation`):**
   * Selenium/Playwright for dynamic content
   * JavaScript-rendered pages
   * Use case: Single-page apps, dynamic dashboards, protected content

5. **API Scraper (`api_scraper`):**
   * Scrape REST APIs without OpenAPI spec
   * Pattern-based API discovery
   * Use case: Public APIs without documentation

6. **Real-Time Monitor (`real_time_monitor`):**
   * Monitor web pages for changes
   * Alert on content updates
   * Use case: Price tracking, status monitoring, content change detection

**Web Connector Management Features:**

* **Add Connector:** Register web data sources with type-specific configuration
* **Multiple Connectors:** Support multiple active web connectors per tenant
* **Rate Limiting:** Configurable rate limits per connector (respect robots.txt)
* **Caching:** Smart caching with TTL to reduce API calls
* **Authentication:** Support API keys, OAuth, cookies for protected content
* **Politeness Policy:** Respect robots.txt, add delays between requests
* **Error Handling:** Retry logic, exponential backoff, error tracking
* **Status Management:** Enable/disable connectors without deletion

**Web Agent Requirements:**

* Real-time web data retrieval on-demand.
* Cache results with configurable TTL.
* Respect rate limits and robots.txt.
* Handle authentication (API keys, OAuth, cookies).
* Parse HTML, JSON, XML, RSS/Atom feeds.
* Extract structured data from web pages.
* Support JavaScript rendering for dynamic content.
* Return citations with URL and timestamp.
* Handle errors gracefully (404, 403, rate limits).
* Support webhook ingestion and storage.

**Example Configurations:**

```json
// Web Search (Google Custom Search)
{
  "connectorType": "web_search",
  "config": {
    "provider": "google_custom_search",
    "apiKey": "encrypted",
    "searchEngineId": "cx=...",
    "maxResults": 10
  },
  "rateLimitConfig": {
    "requestsPerMinute": 10,
    "requestsPerDay": 100
  },
  "cacheConfig": {
    "ttlSeconds": 3600
  }
}

// RSS Feed
{
  "connectorType": "rss_feed",
  "config": {
    "feedUrl": "https://example.com/feed.xml",
    "pollInterval": 3600,
    "maxItems": 50
  }
}

// Browser Automation
{
  "connectorType": "browser_automation",
  "config": {
    "url": "https://example.com/dashboard",
    "waitForSelector": ".content-loaded",
    "screenshot": false,
    "headless": true
  },
  "authConfig": {
    "type": "cookie",
    "cookies": "encrypted"
  }
}

// Webhook Receiver
{
  "connectorType": "webhook",
  "config": {
    "webhookPath": "/webhooks/github",
    "secret": "encrypted",
    "storePayloads": true
  }
}
```

---

## 5. API Endpoints

### `/v1/chat`

**Request:**

```json
{
  "tenantId": "demo",
  "messages": [
    {"role": "user", "content": "What’s our refund rate by month?"}
  ],
  "toolsAllowed": ["retrieval", "sql", "api", "web"],
  "dryRun": true
}
```

**Response:**

```json
{
  "answer": "The refund rate peaked in March at 4.1%",
  "citations": [{"type": "db", "table": "refunds"}],
  "artifacts": {"sql": "SELECT ...", "curl": "curl -H '...'"}
}
```

### `/v1/tools/sql/plan`

* Returns `{sql, risk, estimatedCost, targetConnector}`

### `/v1/admin/connectors/database` (POST)

**Add/Register a new database connector.**

**Request:**

```json
{
  "tenantId": "demo",
  "name": "Analytics DB",
  "description": "Main analytics PostgreSQL database",
  "dbType": "postgresql",
  "connectionString": "postgresql://user:pass@host:5432/dbname", // encrypted in storage
  "readOnly": true,
  "maxRowsPerQuery": 100
}
```

**Response:**

```json
{
  "connectorId": "uuid",
  "status": "active",
  "schemaDiscovered": true,
  "tablesCount": 15,
  "tables": [
    {"name": "customers", "columns": ["customer_id", "name", "email"]},
    {"name": "orders", "columns": ["order_id", "customer_id", "total_amount"]}
  ]
}
```

### `/v1/admin/connectors/database` (GET)

**List all database connectors for a tenant.**

**Query Params:** `tenantId` (required)

**Response:**

```json
{
  "connectors": [
    {
      "connectorId": "uuid",
      "name": "Analytics DB",
      "dbType": "postgresql",
      "status": "active",
      "tablesCount": 15,
      "lastSchemaSync": "2024-01-15T10:00:00Z",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### `/v1/admin/connectors/database/{connectorId}` (GET)

**Get details of a specific database connector.**

**Response:**

```json
{
  "connectorId": "uuid",
  "name": "Analytics DB",
  "description": "Main analytics PostgreSQL database",
  "dbType": "postgresql",
  "status": "active",
  "readOnly": true,
  "maxRowsPerQuery": 100,
  "schema": {
    "tables": [
      {
        "name": "customers",
        "columns": [
          {"name": "customer_id", "type": "INTEGER", "nullable": false},
          {"name": "name", "type": "TEXT", "nullable": false}
        ]
      }
    ]
  },
  "createdAt": "2024-01-15T10:00:00Z",
  "lastSchemaSync": "2024-01-15T10:00:00Z"
}
```

### `/v1/admin/connectors/database/{connectorId}` (PUT)

**Update connector (connection string, read-only flag, limits).**

**Request:**

```json
{
  "status": "inactive", // or "active"
  "readOnly": true,
  "maxRowsPerQuery": 200
}
```

### `/v1/admin/connectors/database/{connectorId}` (DELETE)

**Delete connector (soft delete: set status to 'inactive').**

### `/v1/admin/connectors/database/{connectorId}/sync-schema` (POST)

**Manually trigger schema discovery and refresh.**

### `/v1/tools/api/preview`

* Returns `{curl, jsonBody}`

### `/v1/admin/connectors/ingest`

* **Deprecated:** Triggers ingestion for all formats. Use source-specific sync endpoints instead.

### `/v1/admin/connectors/openapi` (POST)

**Add/Register a new OpenAPI connector.**

**Request:**

```json
{
  "tenantId": "demo",
  "name": "PetStore API",
  "description": "Pet management API",
  "baseUrl": "https://api.petstore.com/v1",
  "openapiSpec": {...}, // or provide "specUrl" or "specFile" (multipart)
  "authType": "api_key",
  "authConfig": {
    "headerName": "X-API-Key",
    "apiKey": "encrypted_value"
  }
}
```

**Response:**

```json
{
  "connectorId": "uuid",
  "status": "active",
  "toolsRegistered": 4,
  "endpoints": [
    {"path": "/pets", "method": "GET", "toolName": "petstore_get_pets"},
    {"path": "/pets", "method": "POST", "toolName": "petstore_create_pet"}
  ]
}
```

### `/v1/admin/connectors/openapi` (GET)

**List all OpenAPI connectors for a tenant.**

**Query Params:** `tenantId` (required)

**Response:**

```json
{
  "connectors": [
    {
      "connectorId": "uuid",
      "name": "PetStore API",
      "status": "active",
      "baseUrl": "https://api.petstore.com/v1",
      "toolsCount": 4,
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### `/v1/admin/connectors/openapi/{connectorId}` (GET)

**Get details of a specific connector.**

**Response:**

```json
{
  "connectorId": "uuid",
  "name": "PetStore API",
  "description": "Pet management API",
  "baseUrl": "https://api.petstore.com/v1",
  "status": "active",
  "openapiSpec": {...},
  "tools": [
    {
      "toolName": "petstore_get_pets",
      "path": "/pets",
      "method": "GET",
      "description": "List all pets"
    }
  ],
  "createdAt": "2024-01-15T10:00:00Z",
  "updatedAt": "2024-01-15T10:00:00Z"
}
```

### `/v1/admin/connectors/openapi/{connectorId}` (PUT)

**Update connector (spec, auth, status).**

**Request:**

```json
{
  "status": "inactive", // or "active"
  "baseUrl": "https://api.petstore.com/v2",
  "authConfig": {...}
}
```

### `/v1/admin/connectors/openapi/{connectorId}` (DELETE)

**Delete connector (soft delete: set status to 'inactive').**

### `/v1/admin/connectors/openapi/{connectorId}/reindex` (POST)

**Re-parse OpenAPI spec and re-register tools (useful after spec updates).**

### `/v1/admin/connectors/document-source` (POST)

**Add/Register a new document source connector.**

**Request:**

```json
{
  "tenantId": "demo",
  "name": "Company Wiki",
  "description": "Internal company documentation wiki",
  "sourceType": "local_fs",
  "config": {
    "path": "/data/docs/wiki",
    "recursive": true
  },
  "fileFilters": {
    "allowedExtensions": [".pdf", ".md", ".docx"],
    "maxFileSizeMb": 50,
    "excludePatterns": ["*.tmp", "*.bak"]
  },
  "autoSync": true,
  "syncSchedule": "0 2 * * *"
}
```

**Alternative source types:**

```json
// S3 bucket
{
  "sourceType": "s3",
  "config": {
    "bucket": "company-docs",
    "prefix": "wiki/",
    "region": "us-east-1",
    "credentials": {...}
  }
}

// Web scraping
{
  "sourceType": "web_scrape",
  "config": {
    "baseUrl": "https://docs.company.com",
    "urlPattern": "https://docs.company.com/**/*.html"
  }
}

// Confluence
{
  "sourceType": "confluence",
  "config": {
    "baseUrl": "https://company.atlassian.net",
    "spaceKeys": ["ENG", "PROD"],
    "apiToken": "encrypted"
  }
}
```

**Response:**

```json
{
  "sourceId": "uuid",
  "status": "syncing",
  "filesDiscovered": 0,
  "syncJobId": "uuid"
}
```

### `/v1/admin/connectors/document-source` (GET)

**List all document sources for a tenant.**

**Query Params:** `tenantId` (required)

**Response:**

```json
{
  "sources": [
    {
      "sourceId": "uuid",
      "name": "Company Wiki",
      "sourceType": "local_fs",
      "status": "active",
      "filesCount": 1250,
      "totalSizeMb": 450,
      "lastSyncAt": "2024-01-15T10:00:00Z",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### `/v1/admin/connectors/document-source/{sourceId}` (GET)

**Get details of a specific document source.**

**Response:**

```json
{
  "sourceId": "uuid",
  "name": "Company Wiki",
  "description": "Internal company documentation wiki",
  "sourceType": "local_fs",
  "status": "active",
  "config": {...},
  "fileFilters": {...},
  "filesCount": 1250,
  "totalSizeMb": 450,
  "lastSyncAt": "2024-01-15T10:00:00Z",
  "recentFiles": [
    {"path": "handbook.pdf", "size": 2048000, "lastModified": "2024-01-15T09:00:00Z"}
  ],
  "createdAt": "2024-01-15T10:00:00Z"
}
```

### `/v1/admin/connectors/document-source/{sourceId}` (PUT)

**Update source (config, filters, sync schedule).**

**Request:**

```json
{
  "status": "inactive",
  "autoSync": false,
  "fileFilters": {
    "allowedExtensions": [".pdf", ".md"]
  }
}
```

### `/v1/admin/connectors/document-source/{sourceId}` (DELETE)

**Delete source (soft delete: set status to 'inactive', optionally delete chunks).**

**Query Params:** `deleteChunks` (boolean, default: false)

### `/v1/admin/connectors/document-source/{sourceId}/sync` (POST)

**Manually trigger synchronization of document source.**

**Response:**

```json
{
  "syncJobId": "uuid",
  "status": "started",
  "estimatedFiles": 1250
}
```

### `/v1/admin/connectors/document-source/{sourceId}/sync/{jobId}` (GET)

**Get sync job status.**

**Response:**

```json
{
  "jobId": "uuid",
  "status": "completed",
  "filesProcessed": 1250,
  "filesSkipped": 5,
  "filesFailed": 2,
  "chunksCreated": 8500,
  "startedAt": "2024-01-15T10:00:00Z",
  "completedAt": "2024-01-15T10:15:00Z"
}
```

### `/v1/admin/connectors/web` (POST)

**Add/Register a new web data connector.**

**Request:**

```json
{
  "tenantId": "demo",
  "name": "Google Search",
  "description": "Web search via Google Custom Search API",
  "connectorType": "web_search",
  "config": {
    "provider": "google_custom_search",
    "apiKey": "encrypted",
    "searchEngineId": "cx=...",
    "maxResults": 10
  },
  "rateLimitConfig": {
    "requestsPerMinute": 10,
    "requestsPerDay": 100
  },
  "cacheConfig": {
    "ttlSeconds": 3600
  }
}
```

**Response:**

```json
{
  "connectorId": "uuid",
  "status": "active",
  "connectorType": "web_search",
  "lastAccessedAt": null
}
```

### `/v1/admin/connectors/web` (GET)

**List all web connectors for a tenant.**

**Query Params:** `tenantId` (required), `connectorType` (optional filter)

**Response:**

```json
{
  "connectors": [
    {
      "connectorId": "uuid",
      "name": "Google Search",
      "connectorType": "web_search",
      "status": "active",
      "lastAccessedAt": "2024-01-15T10:00:00Z",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### `/v1/admin/connectors/web/{connectorId}` (GET)

**Get details of a specific web connector.**

**Response:**

```json
{
  "connectorId": "uuid",
  "name": "Google Search",
  "description": "Web search via Google Custom Search API",
  "connectorType": "web_search",
  "status": "active",
  "config": {...},
  "rateLimitConfig": {...},
  "cacheConfig": {...},
  "lastAccessedAt": "2024-01-15T10:00:00Z",
  "createdAt": "2024-01-15T10:00:00Z"
}
```

### `/v1/admin/connectors/web/{connectorId}` (PUT)

**Update connector (config, rate limits, cache settings).**

**Request:**

```json
{
  "status": "inactive",
  "rateLimitConfig": {
    "requestsPerMinute": 20
  },
  "cacheConfig": {
    "ttlSeconds": 7200
  }
}
```

### `/v1/admin/connectors/web/{connectorId}` (DELETE)

**Delete connector (soft delete: set status to 'inactive').**

### `/v1/tools/web/search` (POST)

**Execute web search using active web search connectors.**

**Request:**

```json
{
  "tenantId": "demo",
  "query": "latest AI developments 2024",
  "connectorId": "uuid", // optional, uses first active if not specified
  "maxResults": 10,
  "useCache": true
}
```

**Response:**

```json
{
  "results": [
    {
      "title": "AI Developments in 2024",
      "url": "https://example.com/article",
      "snippet": "Recent advances in AI...",
      "timestamp": "2024-01-15T10:00:00Z",
      "source": "Google Search"
    }
  ],
  "cached": false,
  "connectorUsed": "uuid"
}
```

### `/v1/tools/web/fetch` (POST)

**Fetch content from a specific URL (with caching).**

**Request:**

```json
{
  "tenantId": "demo",
  "url": "https://example.com/article",
  "connectorId": "uuid", // optional, for browser automation
  "extractText": true,
  "useCache": true
}
```

**Response:**

```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "Extracted text content...",
  "metadata": {
    "author": "John Doe",
    "publishedDate": "2024-01-15",
    "wordCount": 1200
  },
  "cached": true,
  "fetchedAt": "2024-01-15T10:00:00Z"
}
```

### `/v1/tools/web/rss` (GET)

**Get latest items from RSS feed connectors.**

**Query Params:** `tenantId` (required), `connectorId` (optional), `limit` (default: 20)

**Response:**

```json
{
  "feed": {
    "title": "Example Blog",
    "url": "https://example.com/feed.xml"
  },
  "items": [
    {
      "title": "Blog Post Title",
      "url": "https://example.com/post",
      "published": "2024-01-15T09:00:00Z",
      "summary": "Post summary..."
    }
  ],
  "connectorId": "uuid"
}
```

### `/v1/webhooks/{connectorId}` (POST)

**Receive webhook data (public endpoint for webhook connectors).**

**Headers:** `X-Webhook-Secret` (for validation)

**Request Body:** Webhook payload (varies by source)

**Response:**

```json
{
  "received": true,
  "stored": true,
  "webhookId": "uuid",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### `/v1/admin/connectors/web/{connectorId}/webhooks` (GET)

**List received webhooks for a webhook connector.**

**Query Params:** `tenantId` (required), `limit` (default: 50), `since` (optional timestamp)

**Response:**

```json
{
  "webhooks": [
    {
      "webhookId": "uuid",
      "payload": {...},
      "receivedAt": "2024-01-15T10:00:00Z",
      "processed": true
    }
  ]
}
```

---

## 6. Database Query Routing and Multi-Database Support

**How SQL Queries Route to Correct Database:**

1. **Schema-Aware Query Generation:**
   * LLM agent receives schema information from all active database connectors
   * Schema includes: connector name, database type, tables, columns, types
   * Agent generates SQL with awareness of which tables exist in which database
   * Example context: "Analytics DB (PostgreSQL): customers, orders, refunds" vs "Inventory DB (MySQL): products, stock"

2. **Query Routing Strategies:**
   * **Table Name Mapping:** System maintains mapping of table names to connectors
   * **Explicit Connector Selection:** User can specify target database in query
   * **Auto-Detection:** If table exists in only one database, route automatically
   * **Cross-Database Queries:** For queries spanning multiple databases, system can:
     * Execute queries separately and merge results
     * Or suggest using data warehouse/ETL approach

3. **SQL Dialect Generation:**
   * System detects database type (PostgreSQL, MySQL, SQLite, etc.)
   * Generates database-appropriate SQL syntax
   * Handles differences in:
     * Date functions (NOW() vs CURRENT_TIMESTAMP)
     * String concatenation (|| vs CONCAT)
     * LIMIT/OFFSET syntax
     * Data type casting

4. **Schema Discovery and Caching:**
   * On connector registration, system queries INFORMATION_SCHEMA or equivalent
   * Caches schema in `schema_info` JSONB field
   * Periodic refresh via `/sync-schema` endpoint
   * Schema includes: table names, column names/types, constraints, indexes

5. **Connection Management:**
   * Connection pooling per database connector
   * Encrypted connection strings stored in database
   * Read-only mode enforcement per connector
   * Query timeout and row limit enforcement

---

## 7. OpenAPI Tool Registration and Discovery

**How OpenAPI Connectors Become LLM Tools:**

1. **Registration Flow:**
   * Admin adds OpenAPI connector via `/v1/admin/connectors/openapi` (POST)
   * System parses OpenAPI spec and extracts all endpoints
   * Each endpoint is converted to a function tool schema (OpenAI/Anthropic format)
   * Tools are registered with naming convention: `{connector_name}_{operation_id}`
   * Tools stored in database with mapping to connector_id

2. **Tool Schema Generation:**
   * Extract: path, method, parameters, request body, responses
   * Generate function description from OpenAPI `summary`/`description`
   * Convert OpenAPI parameter schemas to JSON Schema
   * Include base URL and auth requirements in tool metadata

3. **Dynamic Tool Loading:**
   * On chat request, system loads all active connectors for tenant
   * Builds tool list from all active connectors
   * Passes tools to LLM agent in tool-calling format
   * LLM can discover and use any registered tool

4. **Tool Execution:**
   * When LLM calls a tool (e.g., `petstore_get_pets`), system:
     * Identifies connector from tool name
     * Retrieves connector config (base URL, auth)
     * Validates parameters against OpenAPI schema
     * Constructs HTTP request
     * Executes (or previews in dry-run mode)
     * Returns response to LLM

5. **Tool Conflict Resolution:**
   * If multiple connectors have same operation_id, prefix with connector name
   * Example: `petstore_get_pets` vs `inventory_get_pets`
   * System validates uniqueness on registration

---

## 8. Web Data Access and Real-Time Retrieval

**How Web Data Connectors Work:**

1. **Web Search Integration:**
   * LLM agent can trigger web searches for current information
   * Results are cached with TTL to reduce API calls
   * Citations include search provider and URL
   * Example: "What's the latest news about X?" → triggers web search

2. **RSS Feed Polling:**
   * RSS feeds are polled periodically (configurable interval)
   * New items are stored and indexed for RAG
   * Can query: "What's new in the engineering blog this week?"

3. **Webhook Ingestion:**
   * Webhooks are received and stored
   * Payloads are indexed and searchable
   * Can query: "Show me recent GitHub events"

4. **Browser Automation:**
   * For JavaScript-rendered content
   * Handles authentication (cookies, OAuth)
   * Screenshots optional for visual content
   * Extracts structured data from dynamic pages

5. **Caching Strategy:**
   * Web search results cached by query
   * URL content cached by URL
   * TTL configurable per connector
   * Cache invalidation on demand

6. **Rate Limiting:**
   * Respects API rate limits
   * Configurable per connector
   * Queue requests if limit exceeded
   * Respects robots.txt for scraping

---

## 9. Document Source Retrieval and RAG

**How Document Sources Are Searched:**

1. **Multi-Source Search:**
   * Search across all active document sources for a tenant
   * Can filter by specific source(s) if needed
   * Results include source attribution in citations

2. **Hybrid Search Strategy:**
   * **BM25 + Vector:** Hybrid search combining keyword (BM25) and semantic (vector) search
   * **Source-Aware:** Results tagged with source name and file path
   * **Re-ranking:** Top 50 results → re-rank → top 8
   * **Diversity:** Ensure results from multiple sources when possible

3. **Citation Format:**
   * Include source name: `(Company Wiki: handbook.pdf p.4, lines 120–137)`
   * Or: `(Product Docs: api-reference.md, section "Authentication")`
   * Metadata includes: source_id, file_path, page, line numbers, headings

4. **Source Filtering:**
   * Users can specify source in query: "Search in Company Wiki for..."
   * System can auto-detect source from context
   * Admin can enable/disable sources without re-indexing

5. **Incremental Updates:**
   * New files in sources are automatically indexed (if auto-sync enabled)
   * Changed files trigger re-chunking and re-embedding
   * Deleted files are marked inactive (soft delete)

---

## 10. Retrieval and RAG

* Hybrid search (BM25 + vector) across all active sources.
* Re-rank top 50 → top 8.
* Require at least 3 citations per answer.
* Disallow fabricated sources.
* Source attribution in all citations.

---

## 11. Prompts and Guardrails

**System Prompt Summary:**

* Role: BridgeMind, a tool-using enterprise assistant.
* Rules: cite sources, never invent citations, prefer tools over guessing.
* Redact secrets.
* Ask before side effects.

**SQL Guardrails:**

* Default read-only; limit 100 rows (configurable per connector).
* Explain plan before execution.
* Support multiple database connectors per tenant.
* Auto-detect database type and generate appropriate SQL dialect.
* Schema-aware query generation (validate tables/columns exist).
* Query routing to correct database connector.
* Connection string encryption at rest.
* Per-connector read-only enforcement.

**API Guardrails:**

* Validate schema; default dry-run.
* Support multiple OpenAPI connectors per tenant.
* Tool name collision detection (prefix with connector name).
* Route API calls to correct base URL based on connector.
* Per-connector auth configuration.

---

## 12. Security and Tenancy

* Tenant isolation via ID prefixes.
* Secrets stored in `.env` or Vault.
* Audit table for all tool calls.
* Logs redacted for PII.

---

## 13. Observability

* OpenTelemetry traces (chat → retrieval → tool → DB/API).
* Metrics: token_usage, latency, tool_success_rate.

---

## 14. Evaluation

| Area | Metric                   | Target |
| ---- | ------------------------ | ------ |
| RAG  | Correct citations        | ≥80%   |
| SQL  | Execution success        | ≥90%   |
| API  | Valid OpenAPI compliance | ≥95%   |

---

## 15. UI (MVP)

* Chat interface with streaming.
* Tabs: **Answer**, **Sources**, **SQL**, **API**, **Data**.
* Admin panel: 
  * Re-index connectors.
  * Add/Edit/Delete OpenAPI connectors.
  * Add/Edit/Delete database connectors.
  * Add/Edit/Delete document source connectors.
  * Add/Edit/Delete web data connectors.
  * View registered tools from all connectors.
  * View database schemas and sync status.
  * View document source sync status and file counts.
  * View web connector usage and cache status.
  * Test connector endpoints.
  * Test database connections.
  * Trigger document source synchronization.
  * Test web search and fetch operations.
* Settings: toggle dry-run, select model.

---

## 16. Deliverables

1. Docker Compose setup (Postgres + API).
2. Ingestion for all data types.
3. Chat API and minimal React UI.
4. Evaluation scripts (RAG, SQL, API).
5. End-to-end tests with citations.

---

## 17. Acceptance Criteria

* Ingestion of all sample sources works.
* Questions on refund policy cite correct PDF spans.
* SQL generation works for refund analytics.
* API preview produces valid curl.
* All logs sanitized and auditable.
* **OpenAPI Connector Management:**
  * Users can add new OpenAPI specs via admin API.
  * Multiple connectors can be active simultaneously.
  * Tools from all active connectors are available to LLM.
  * Connector CRUD operations work correctly.
  * Tool name collisions are prevented.
  * API calls route to correct base URL.
* **Database Connector Management:**
  * Users can add new database connectors via admin API.
  * Multiple database connectors can be active simultaneously.
  * Schema discovery works for PostgreSQL, MySQL, SQLite, etc.
  * SQL queries route to correct database connector.
  * Database-specific SQL dialects are generated correctly.
  * Connection strings are encrypted at rest.
  * Schema caching and sync works properly.
* **Document Source Connector Management:**
  * Users can add new document sources via admin API (local FS, S3, web, etc.).
  * Multiple document sources can be active simultaneously.
  * Files are automatically discovered, chunked, and indexed.
  * Citations include source attribution (e.g., "Company Wiki: file.pdf").
  * Auto-sync and incremental updates work correctly.
  * File filtering and size limits are enforced.
  * Source-specific search and filtering works.
* **Web Data Connector Management:**
  * Users can add web data connectors (web search, RSS, webhooks, browser automation).
  * Multiple web connectors can be active simultaneously.
  * Real-time web data retrieval works on-demand.
  * Rate limiting and caching are properly enforced.
  * Web search results are returned with citations and URLs.
  * RSS feeds are polled and stored for querying.
  * Webhooks are received and stored for later querying.
  * Browser automation handles dynamic content correctly.
  * Caching reduces redundant API calls.
  * robots.txt and politeness policies are respected.

---

**Next Step:** Transform this spec into a runnable starter repo scaffold (Docker + sample data + API + UI) for Codex or another AI development environment.
