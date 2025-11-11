"""
SQL tool endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from bridgemind.api.database import get_db
from bridgemind.api.services.sql_agent import SQLAgent

router = APIRouter()

# Initialize SQL agent (singleton)
_sql_agent = None

def get_sql_agent() -> SQLAgent:
    """Get or create SQL agent instance"""
    global _sql_agent
    if _sql_agent is None:
        _sql_agent = SQLAgent()
    return _sql_agent


class SQLPlanRequest(BaseModel):
    tenantId: str
    query: str
    connectorId: Optional[str] = None


class SQLPlanResponse(BaseModel):
    sql: str
    risk: str
    estimatedCost: Optional[str] = None
    targetConnector: Optional[str] = None
    error: Optional[str] = None


@router.post("/plan", response_model=SQLPlanResponse)
async def plan_sql(
    request: SQLPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Plan SQL query execution.
    Returns SQL, risk assessment, and target connector.
    """
    sql_agent = get_sql_agent()
    
    result = await sql_agent.generate_sql(
        query=request.query,
        tenant_id=request.tenantId,
        db=db,
        connector_id=request.connectorId
    )
    
    return SQLPlanResponse(
        sql=result.get("sql", "SELECT 1;"),
        risk=result.get("risk", "low"),
        estimatedCost=result.get("estimatedCost", "N/A"),
        targetConnector=result.get("targetConnector"),
        error=result.get("error")
    )

