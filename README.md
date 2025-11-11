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
      api_agent.py
      file_agent.py
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
  tests/
    e2e/
    unit/
```

---

## 4. Data Connectors

### 4.1 PostgreSQL Database

**Purpose:** SQL agent for analytics.

**Schema:**

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

**Seed:** 25 customers, 120 orders, 12 refunds.

**Rules:** Read-only queries by default; limit 100 rows; return SQL + provenance.

---

### 4.2 OpenAPI Specification

**File:** `petstore.yaml` (OpenAPI 3.0)

Endpoints:

* `GET /pets?limit={n}`
* `POST /pets`
* `GET /pets/{id}`
* `POST /appointments`

**Auth:** API key header `X-API-Key`

**API Agent Requirements:**

* Validate params against schema.
* Default to **preview mode** (show curl + JSON).
* Mask secrets in logs.

---

### 4.3 Documents and Files

Each file type will be ingested and indexed with metadata `{tenantId, uri, title, format, page, lineStart, lineEnd, section, headings[], ingestion_ts}`.

| Format   | File                 | Purpose                           |
| -------- | -------------------- | --------------------------------- |
| PDF      | `handbook.pdf`       | Policy with sections for citation |
| Markdown | `wiki_page.md`       | Architecture overview             |
| CSV      | `pricing.csv`        | Product price table               |
| DOCX     | `faq.docx`           | FAQs for NLP extraction           |
| HTML     | `release_notes.html` | Structured change log             |
| TXT      | `readme.txt`         | Simple plain text example         |
| JSON     | `product.json`       | Nested data test                  |
| XLSX     | `inventory.xlsx`     | Multi-sheet stock/backorders      |

**File Agent Requirements:**

* Chunk text 700–1,000 tokens with headings.
* Extract and preserve page/line info (PDF).
* Store original file + embeddings.
* Return citations like `(handbook.pdf p.4, lines 120–137)`.

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
  "toolsAllowed": ["retrieval", "sql", "api"],
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

* Returns `{sql, risk, estimatedCost}`

### `/v1/tools/api/preview`

* Returns `{curl, jsonBody}`

### `/v1/admin/connectors/ingest`

* Triggers ingestion for all formats.

---

## 6. Retrieval and RAG

* Hybrid search (BM25 + vector).
* Re-rank top 50 → top 8.
* Require at least 3 citations per answer.
* Disallow fabricated sources.

---

## 7. Prompts and Guardrails

**System Prompt Summary:**

* Role: BridgeMind, a tool-using enterprise assistant.
* Rules: cite sources, never invent citations, prefer tools over guessing.
* Redact secrets.
* Ask before side effects.

**SQL Guardrails:**

* Default read-only; limit 100 rows.
* Explain plan before execution.

**API Guardrails:**

* Validate schema; default dry-run.

---

## 8. Security and Tenancy

* Tenant isolation via ID prefixes.
* Secrets stored in `.env` or Vault.
* Audit table for all tool calls.
* Logs redacted for PII.

---

## 9. Observability

* OpenTelemetry traces (chat → retrieval → tool → DB/API).
* Metrics: token_usage, latency, tool_success_rate.

---

## 10. Evaluation

| Area | Metric                   | Target |
| ---- | ------------------------ | ------ |
| RAG  | Correct citations        | ≥80%   |
| SQL  | Execution success        | ≥90%   |
| API  | Valid OpenAPI compliance | ≥95%   |

---

## 11. UI (MVP)

* Chat interface with streaming.
* Tabs: **Answer**, **Sources**, **SQL**, **API**, **Data**.
* Admin panel: re-index connectors.
* Settings: toggle dry-run, select model.

---

## 12. Deliverables

1. Docker Compose setup (Postgres + API).
2. Ingestion for all data types.
3. Chat API and minimal React UI.
4. Evaluation scripts (RAG, SQL, API).
5. End-to-end tests with citations.

---

## 13. Acceptance Criteria

* Ingestion of all sample sources works.
* Questions on refund policy cite correct PDF spans.
* SQL generation works for refund analytics.
* API preview produces valid curl.
* All logs sanitized and auditable.

---

**Next Step:** Transform this spec into a runnable starter repo scaffold (Docker + sample data + API + UI) for Codex or another AI development environment.
