"""
Chat endpoint - Main interface for LLM agent interactions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()


class Message(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    tenantId: str
    messages: List[Message]
    toolsAllowed: List[str] = ["retrieval", "sql", "api", "web"]
    dryRun: bool = False


class Citation(BaseModel):
    type: str  # "db", "api", "document", "web"
    source: Optional[str] = None
    table: Optional[str] = None
    url: Optional[str] = None
    file: Optional[str] = None
    page: Optional[int] = None
    lines: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    artifacts: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for LLM agent interactions.
    
    Supports multiple tools: retrieval, sql, api, web
    """
    # TODO: Implement orchestrator logic
    # This will integrate with:
    # - LLM agent (OpenAI/Anthropic)
    # - Retrieval service (RAG)
    # - SQL agent
    # - API agent
    # - Web agent
    
    # Placeholder response
    return ChatResponse(
        answer="This is a placeholder response. Implementation in progress.",
        citations=[],
        artifacts={}
    )

