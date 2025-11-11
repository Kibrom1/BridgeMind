"""
Admin connector management endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
from datetime import datetime

from bridgemind.api.database import get_db
from bridgemind.api.models.database import DatabaseConnector

router = APIRouter()


# Database Connector Models
class DatabaseConnectorCreate(BaseModel):
    tenantId: str
    name: str
    description: Optional[str] = None
    dbType: str
    connectionString: str
    readOnly: bool = True
    maxRowsPerQuery: int = 100


class DatabaseConnectorResponse(BaseModel):
    connectorId: str
    status: str
    schemaDiscovered: bool
    tablesCount: int
    tables: List[Dict[str, Any]]


# OpenAPI Connector Models
class OpenAPIConnectorCreate(BaseModel):
    tenantId: str
    name: str
    description: Optional[str] = None
    baseUrl: str
    openapiSpec: Dict[str, Any]
    authType: str = "none"
    authConfig: Optional[Dict[str, Any]] = None


class OpenAPIConnectorResponse(BaseModel):
    connectorId: str
    status: str
    toolsRegistered: int
    endpoints: List[Dict[str, Any]]


# Document Source Models
class DocumentSourceCreate(BaseModel):
    tenantId: str
    name: str
    description: Optional[str] = None
    sourceType: str
    config: Dict[str, Any]
    fileFilters: Optional[Dict[str, Any]] = None
    autoSync: bool = False
    syncSchedule: Optional[str] = None


class DocumentSourceResponse(BaseModel):
    sourceId: str
    status: str
    filesDiscovered: int
    syncJobId: Optional[str] = None


# Web Connector Models
class WebConnectorCreate(BaseModel):
    tenantId: str
    name: str
    description: Optional[str] = None
    connectorType: str
    config: Dict[str, Any]
    rateLimitConfig: Optional[Dict[str, Any]] = None
    cacheConfig: Optional[Dict[str, Any]] = None


class WebConnectorResponse(BaseModel):
    connectorId: str
    status: str
    connectorType: str
    lastAccessedAt: Optional[str] = None


# Database Connector Endpoints
@router.post("/database", response_model=DatabaseConnectorResponse)
async def create_database_connector(
    connector: DatabaseConnectorCreate,
    db: Session = Depends(get_db)
):
    """Add/Register a new database connector"""
    try:
        # Check if connector with same name already exists
        existing = db.query(DatabaseConnector).filter(
            DatabaseConnector.tenant_id == connector.tenantId,
            DatabaseConnector.name == connector.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Connector with name '{connector.name}' already exists for this tenant"
            )
        
        # Test database connection
        try:
            from sqlalchemy import create_engine, inspect
            test_engine = create_engine(connector.connectionString, pool_pre_ping=True, poolclass=None)
            with test_engine.connect() as conn:
                # Test connection
                conn.execute(text("SELECT 1"))
                conn.commit()
                
                # Discover schema if connection successful
                inspector = inspect(test_engine)
                tables = inspector.get_table_names()
                schema_info = {
                    "tables": [
                        {
                            "name": table,
                            "columns": [
                                {
                                    "name": col["name"],
                                    "type": str(col["type"]),
                                    "nullable": col["nullable"]
                                }
                                for col in inspector.get_columns(table)
                            ]
                        }
                        for table in tables
                    ]
                }
                test_engine.dispose()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect to database: {str(e)}"
            )
        
        # Create connector record
        db_connector = DatabaseConnector(
            tenant_id=connector.tenantId,
            name=connector.name,
            description=connector.description,
            db_type=connector.dbType,
            connection_string=connector.connectionString,  # TODO: Encrypt this
            schema_info=schema_info,
            status='active',
            read_only=connector.readOnly,
            max_rows_per_query=connector.maxRowsPerQuery,
            last_schema_sync=datetime.utcnow()
        )
        
        db.add(db_connector)
        db.commit()
        db.refresh(db_connector)
        
        return DatabaseConnectorResponse(
            connectorId=str(db_connector.connector_id),
            status=db_connector.status,
            schemaDiscovered=True,
            tablesCount=len(schema_info.get("tables", [])),
            tables=[
                {"name": table["name"], "columns": [col["name"] for col in table["columns"]]}
                for table in schema_info.get("tables", [])[:10]  # Limit to first 10 for response
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create connector: {str(e)}"
        )


@router.get("/database")
async def list_database_connectors(
    tenantId: str = Query(...),
    db: Session = Depends(get_db)
):
    """List all database connectors for a tenant"""
    connectors = db.query(DatabaseConnector).filter(
        DatabaseConnector.tenant_id == tenantId
    ).all()
    
    return {
        "connectors": [
            {
                "connectorId": str(conn.connector_id),
                "name": conn.name,
                "dbType": conn.db_type,
                "status": conn.status,
                "tablesCount": len(conn.schema_info.get("tables", [])) if conn.schema_info else 0,
                "lastSchemaSync": conn.last_schema_sync.isoformat() if conn.last_schema_sync else None,
                "createdAt": conn.created_at.isoformat() if conn.created_at else None
            }
            for conn in connectors
        ]
    }


@router.get("/database/{connectorId}")
async def get_database_connector(
    connectorId: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific database connector"""
    try:
        connector_id = int(connectorId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connector ID")
    
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.connector_id == connector_id
    ).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    return {
        "connectorId": str(connector.connector_id),
        "name": connector.name,
        "description": connector.description,
        "dbType": connector.db_type,
        "status": connector.status,
        "readOnly": connector.read_only,
        "maxRowsPerQuery": connector.max_rows_per_query,
        "schema": connector.schema_info or {"tables": []},
        "createdAt": connector.created_at.isoformat() if connector.created_at else None,
        "lastSchemaSync": connector.last_schema_sync.isoformat() if connector.last_schema_sync else None
    }


@router.put("/database/{connectorId}")
async def update_database_connector(connectorId: str, updates: Dict[str, Any]):
    """Update connector"""
    # TODO: Implement update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/database/{connectorId}")
async def delete_database_connector(
    connectorId: str,
    db: Session = Depends(get_db)
):
    """Delete connector (hard delete)"""
    try:
        connector_id = int(connectorId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connector ID")
    
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.connector_id == connector_id
    ).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    try:
        db.delete(connector)
        db.commit()
        return {"message": f"Connector '{connector.name}' deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete connector: {str(e)}"
        )


@router.post("/database/{connectorId}/sync-schema")
async def sync_database_schema(connectorId: str):
    """Manually trigger schema discovery and refresh"""
    # TODO: Implement schema sync
    raise HTTPException(status_code=501, detail="Not implemented yet")


# OpenAPI Connector Endpoints
@router.post("/openapi", response_model=OpenAPIConnectorResponse)
async def create_openapi_connector(connector: OpenAPIConnectorCreate):
    """Add/Register a new OpenAPI connector"""
    # TODO: Implement OpenAPI connector creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/openapi")
async def list_openapi_connectors(tenantId: str = Query(...)):
    """List all OpenAPI connectors for a tenant"""
    # TODO: Implement listing
    return {"connectors": []}


@router.get("/openapi/{connectorId}")
async def get_openapi_connector(connectorId: str):
    """Get details of a specific connector"""
    # TODO: Implement get
    raise HTTPException(status_code=404, detail="Connector not found")


@router.put("/openapi/{connectorId}")
async def update_openapi_connector(connectorId: str, updates: Dict[str, Any]):
    """Update connector"""
    # TODO: Implement update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/openapi/{connectorId}")
async def delete_openapi_connector(connectorId: str):
    """Delete connector (soft delete)"""
    # TODO: Implement delete
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/openapi/{connectorId}/reindex")
async def reindex_openapi_connector(connectorId: str):
    """Re-parse OpenAPI spec and re-register tools"""
    # TODO: Implement reindex
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Document Source Endpoints
@router.post("/document-source", response_model=DocumentSourceResponse)
async def create_document_source(source: DocumentSourceCreate):
    """Add/Register a new document source connector"""
    # TODO: Implement document source creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/document-source")
async def list_document_sources(tenantId: str = Query(...)):
    """List all document sources for a tenant"""
    # TODO: Implement listing
    return {"sources": []}


@router.get("/document-source/{sourceId}")
async def get_document_source(sourceId: str):
    """Get details of a specific document source"""
    # TODO: Implement get
    raise HTTPException(status_code=404, detail="Source not found")


@router.put("/document-source/{sourceId}")
async def update_document_source(sourceId: str, updates: Dict[str, Any]):
    """Update source"""
    # TODO: Implement update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/document-source/{sourceId}")
async def delete_document_source(sourceId: str, deleteChunks: bool = False):
    """Delete source (soft delete)"""
    # TODO: Implement delete
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/document-source/{sourceId}/sync")
async def sync_document_source(sourceId: str):
    """Manually trigger synchronization of document source"""
    # TODO: Implement sync
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/document-source/{sourceId}/sync/{jobId}")
async def get_sync_job_status(sourceId: str, jobId: str):
    """Get sync job status"""
    # TODO: Implement job status
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Web Connector Endpoints
@router.post("/web", response_model=WebConnectorResponse)
async def create_web_connector(connector: WebConnectorCreate):
    """Add/Register a new web data connector"""
    # TODO: Implement web connector creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/web")
async def list_web_connectors(tenantId: str = Query(...), connectorType: Optional[str] = None):
    """List all web connectors for a tenant"""
    # TODO: Implement listing
    return {"connectors": []}


@router.get("/web/{connectorId}")
async def get_web_connector(connectorId: str):
    """Get details of a specific web connector"""
    # TODO: Implement get
    raise HTTPException(status_code=404, detail="Connector not found")


@router.put("/web/{connectorId}")
async def update_web_connector(connectorId: str, updates: Dict[str, Any]):
    """Update connector"""
    # TODO: Implement update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/web/{connectorId}")
async def delete_web_connector(connectorId: str):
    """Delete connector (soft delete)"""
    # TODO: Implement delete
    raise HTTPException(status_code=501, detail="Not implemented yet")

