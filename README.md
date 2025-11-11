# BridgeMind – Pre-Coding Requirements Document

## Overview

BridgeMind is an AI agent that unifies structured and unstructured data sources—including APIs, documentation, and databases—into a single intelligent query interface. This document defines the **detailed requirements** to scaffold BridgeMind for development, including one of each data source type: a database, OpenAPI specification, document, wiki page, CSV, and other formats.

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for UI development)

### Running with Docker

```bash
# Start all services
docker-compose -f infra/docker-compose.yml up -d

# View logs
docker-compose -f infra/docker-compose.yml logs -f

# Stop services
docker-compose -f infra/docker-compose.yml down
```

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
# (Connect to postgres and run migration files in order)

# Start API server
uvicorn bridgemind.api.main:app --reload

# Start UI (in separate terminal)
cd bridgemind/ui
npm install
npm start
```

### API Endpoints

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- UI: http://localhost:3000

---

## Project Structure

```
bridgemind/
  api/
    main.py              # FastAPI application
    routes/              # API route handlers
    services/            # Business logic services
  ui/                    # React frontend
  data_samples/          # Sample data for testing
  infra/                 # Infrastructure configs
    docker-compose.yml
    migrations/          # Database migrations
  tests/                 # Test files
```

---

## Development Status

🚧 **In Progress** - Initial scaffolding complete. Core functionality implementation in progress.

### Completed
- ✅ Project structure
- ✅ Docker Compose setup
- ✅ Database migrations
- ✅ FastAPI route stubs
- ✅ Sample data files

### In Progress
- 🔄 Database connection and models
- 🔄 Connector manager implementations
- 🔄 LLM agent integration
- 🔄 RAG implementation

### TODO
- ⏳ React UI components
- ⏳ Authentication
- ⏳ Observability setup
- ⏳ End-to-end tests

---

For detailed requirements, see the full [README.md](README.md) document.
