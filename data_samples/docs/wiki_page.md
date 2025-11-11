# BridgeMind Architecture Overview

## Introduction

BridgeMind is an AI agent that unifies structured and unstructured data sources into a single intelligent query interface. This document provides an overview of the system architecture.

## Core Components

### 1. API Layer
The API layer is built with FastAPI and provides REST endpoints for:
- Chat interactions with the LLM agent
- Connector management (databases, APIs, documents, web)
- Tool execution (SQL, API calls, web search)

### 2. Service Layer
The service layer contains:
- **Orchestrator**: Coordinates between different agents and tools
- **Retrieval Service**: Handles RAG (Retrieval Augmented Generation)
- **SQL Agent**: Generates and executes SQL queries
- **API Agent**: Executes API calls based on OpenAPI specs
- **File Agent**: Processes and indexes documents
- **Web Agent**: Handles web search and data retrieval

### 3. Connector Managers
Each connector type has a dedicated manager:
- Database Connector Manager
- API Connector Manager
- Document Source Manager
- Web Connector Manager

## Data Flow

1. User sends a query via the chat endpoint
2. Orchestrator determines which tools are needed
3. Appropriate agents are invoked (SQL, API, retrieval, web)
4. Results are aggregated and returned with citations
5. LLM generates a natural language response

## Security

- Tenant isolation via ID prefixes
- Encrypted connection strings and secrets
- Audit logging for all tool calls
- PII redaction in logs

## Observability

- OpenTelemetry for distributed tracing
- Metrics for token usage, latency, and success rates
- Structured logging

