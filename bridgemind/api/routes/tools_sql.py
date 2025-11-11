"""
SQL tool endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SQLPlanRequest(BaseModel):
    tenantId: str
    query: str
    connectorId: Optional[str] = None


class SQLPlanResponse(BaseModel):
    sql: str
    risk: str
    estimatedCost: Optional[str] = None
    targetConnector: Optional[str] = None


@router.post("/plan", response_model=SQLPlanResponse)
async def plan_sql(request: SQLPlanRequest):
    """
    Plan SQL query execution.
    Returns SQL, risk assessment, and target connector.
    """
    # TODO: Implement SQL planning
    return SQLPlanResponse(
        sql="SELECT 1;",
        risk="low",
        estimatedCost="N/A",
        targetConnector=None
    )

