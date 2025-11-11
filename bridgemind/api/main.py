"""
BridgeMind API - Main FastAPI application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from bridgemind.api.routes import chat, admin_connectors, tools_sql, tools_api

app = FastAPI(
    title="BridgeMind API",
    description="AI agent that unifies structured and unstructured data sources",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(admin_connectors.router, prefix="/v1/admin/connectors", tags=["admin"])
app.include_router(tools_sql.router, prefix="/v1/tools/sql", tags=["tools"])
app.include_router(tools_api.router, prefix="/v1/tools/api", tags=["tools"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "BridgeMind API"}


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "BridgeMind API",
        "version": "0.1.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

