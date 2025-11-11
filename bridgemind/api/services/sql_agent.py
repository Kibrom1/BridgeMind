"""
SQL Agent - Generates and executes SQL queries
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, inspect
import re

# Load environment variables
from dotenv import load_dotenv

# Try to load .env file from project root
# Path calculation: bridgemind/api/services/sql_agent.py -> ../../.. -> root
_current_file = Path(__file__).resolve()
env_path = _current_file.parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback: try current directory and common locations
    load_dotenv()  # Current directory
    load_dotenv(Path.cwd() / '.env')  # Explicit current working directory

# Try OpenAI first, fallback to Anthropic
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from bridgemind.api.models.database import DatabaseConnector


class SQLAgent:
    """Agent for SQL query generation and execution"""
    
    def __init__(self):
        # Initialize LLM client (prefer OpenAI, fallback to Anthropic)
        self.llm_client = None
        self.llm_provider = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client - can be called again to reload env vars"""
        # Reload environment variables in case they changed
        _current_file = Path(__file__).resolve()
        env_path = _current_file.parent.parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
        else:
            # Try multiple locations
            load_dotenv(override=True)  # Current directory
            load_dotenv(Path.cwd() / '.env', override=True)  # Explicit cwd
        
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if OPENAI_AVAILABLE and openai_key:
            try:
                # Support custom base URL (e.g., for aimlapi or other OpenAI-compatible services)
                base_url = os.getenv("OPENAI_BASE_URL", None)
                if base_url:
                    self.llm_client = OpenAI(api_key=openai_key, base_url=base_url)
                else:
                    self.llm_client = OpenAI(api_key=openai_key)
                self.llm_provider = "openai"
                return
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
        
        if ANTHROPIC_AVAILABLE and anthropic_key:
            try:
                self.llm_client = Anthropic(api_key=anthropic_key)
                self.llm_provider = "anthropic"
                return
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
        
        # No LLM configured
        self.llm_provider = None
        self.llm_client = None
    
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """Format database schema information for LLM prompt"""
        if not schema_info or "tables" not in schema_info:
            return "No schema information available."
        
        schema_text = "Database Schema:\n"
        for table in schema_info.get("tables", []):
            table_name = table.get("name", "")
            columns = table.get("columns", [])
            
            schema_text += f"\nTable: {table_name}\n"
            schema_text += "  Columns:\n"
            for col in columns:
                col_name = col.get("name", "")
                col_type = col.get("type", "")
                nullable = col.get("nullable", True)
                schema_text += f"    - {col_name} ({col_type})"
                if not nullable:
                    schema_text += " NOT NULL"
                schema_text += "\n"
        
        return schema_text
    
    def _generate_sql_with_openai(self, query: str, schema_text: str, db_type: str) -> str:
        """Generate SQL using OpenAI"""
        prompt = f"""You are a SQL expert. Generate a SQL query based on the natural language request.

Database Type: {db_type}

{schema_text}

Natural Language Query: {query}

Instructions:
1. Generate a valid SQL query for the {db_type} database
2. Use only SELECT statements (read-only queries)
3. Use proper table and column names from the schema above
4. Include appropriate JOINs, WHERE clauses, and aggregations as needed
5. Return ONLY the SQL query, no explanations or markdown formatting
6. Do not include any comments or additional text

SQL Query:"""

        response = self.llm_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a SQL expert that generates accurate, read-only SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql = response.choices[0].message.content.strip()
        # Clean up SQL (remove markdown code blocks if present)
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```\s*$', '', sql)
        sql = sql.strip()
        
        return sql
    
    def _generate_sql_with_anthropic(self, query: str, schema_text: str, db_type: str) -> str:
        """Generate SQL using Anthropic"""
        prompt = f"""You are a SQL expert. Generate a SQL query based on the natural language request.

Database Type: {db_type}

{schema_text}

Natural Language Query: {query}

Instructions:
1. Generate a valid SQL query for the {db_type} database
2. Use only SELECT statements (read-only queries)
3. Use proper table and column names from the schema above
4. Include appropriate JOINs, WHERE clauses, and aggregations as needed
5. Return ONLY the SQL query, no explanations or markdown formatting
6. Do not include any comments or additional text

SQL Query:"""

        response = self.llm_client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        sql = response.content[0].text.strip()
        # Clean up SQL (remove markdown code blocks if present)
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```\s*$', '', sql)
        sql = sql.strip()
        
        return sql
    
    def _assess_risk(self, sql: str, read_only: bool, max_rows: int) -> str:
        """Assess risk level of SQL query"""
        sql_upper = sql.upper().strip()
        
        # Check for write operations
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in write_keywords):
            return "high"
        
        # Check if read-only mode is enforced
        if not read_only:
            return "medium"
        
        # Check for potentially expensive operations
        expensive_keywords = ['CROSS JOIN', 'CARTESIAN', 'FULL OUTER JOIN']
        if any(keyword in sql_upper for keyword in expensive_keywords):
            return "medium"
        
        return "low"
    
    async def generate_sql(
        self,
        query: str,
        tenant_id: str,
        db: Session,
        connector_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language.
        
        Args:
            query: Natural language query
            tenant_id: Tenant identifier
            db: Database session
            connector_id: Optional specific database connector
            
        Returns:
            Dictionary with SQL, risk assessment, and target connector
        """
        # Get database connectors
        connectors = db.query(DatabaseConnector).filter(
            DatabaseConnector.tenant_id == tenant_id,
            DatabaseConnector.status == 'active'
        ).all()
        
        if not connectors:
            return {
                "sql": "-- No active database connectors found",
                "risk": "low",
                "targetConnector": None,
                "error": "No active database connectors available"
            }
        
        # If connector_id specified, use that one
        target_connector = None
        if connector_id:
            try:
                connector_id_int = int(connector_id)
                target_connector = next(
                    (c for c in connectors if c.connector_id == connector_id_int),
                    None
                )
            except ValueError:
                pass
        
        # Otherwise, use the first available connector
        if not target_connector:
            target_connector = connectors[0]
        
        # Get schema information
        schema_info = target_connector.schema_info or {}
        schema_text = self._format_schema_for_prompt(schema_info)
        db_type = target_connector.db_type or "postgresql"
        
        # Generate SQL using LLM
        if not self.llm_provider:
            # No LLM configured - return a simple placeholder
            return {
                "sql": "-- LLM not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.",
                "risk": "low",
                "targetConnector": str(target_connector.connector_id),
                "error": "LLM not configured"
            }
        
        try:
            if self.llm_provider == "openai":
                sql = self._generate_sql_with_openai(query, schema_text, db_type)
            elif self.llm_provider == "anthropic":
                sql = self._generate_sql_with_anthropic(query, schema_text, db_type)
            else:
                sql = "-- LLM provider not available"
        except Exception as e:
            return {
                "sql": f"-- Error generating SQL: {str(e)}",
                "risk": "low",
                "targetConnector": str(target_connector.connector_id),
                "error": str(e)
            }
        
        # Assess risk
        risk = self._assess_risk(
            sql,
            target_connector.read_only or True,
            target_connector.max_rows_per_query or 100
        )
        
        return {
            "sql": sql,
            "risk": risk,
            "targetConnector": str(target_connector.connector_id),
            "estimatedCost": "N/A"  # Could be enhanced with query plan analysis
        }
    
    async def execute_sql(
        self,
        sql: str,
        connector_id: str,
        tenant_id: str,
        db: Session,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Execute SQL query on specified database connector.
        
        Args:
            sql: SQL query to execute
            connector_id: Database connector ID
            tenant_id: Tenant identifier
            db: Database session
            dry_run: If True, only return plan without execution
            
        Returns:
            Query results or execution plan
        """
        try:
            connector_id_int = int(connector_id)
        except ValueError:
            return {
                "rows": [],
                "rowCount": 0,
                "sql": sql,
                "error": "Invalid connector ID"
            }
        
        connector = db.query(DatabaseConnector).filter(
            DatabaseConnector.connector_id == connector_id_int,
            DatabaseConnector.tenant_id == tenant_id
        ).first()
        
        if not connector:
            return {
                "rows": [],
                "rowCount": 0,
                "sql": sql,
                "error": "Connector not found"
            }
        
        # Validate query (read-only check)
        sql_upper = sql.upper().strip()
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_upper for keyword in write_keywords):
            return {
                "rows": [],
                "rowCount": 0,
                "sql": sql,
                "error": "Write operations are not allowed"
            }
        
        if dry_run:
            # Return execution plan
            return {
                "rows": [],
                "rowCount": 0,
                "sql": sql,
                "plan": "Dry run mode - query not executed"
            }
        
        # Execute query
        try:
            engine = create_engine(connector.connection_string, pool_pre_ping=True)
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = [dict(row._mapping) for row in result]
                
                # Apply row limit
                max_rows = connector.max_rows_per_query or 100
                if len(rows) > max_rows:
                    rows = rows[:max_rows]
                    return {
                        "rows": rows,
                        "rowCount": len(rows),
                        "sql": sql,
                        "warning": f"Results limited to {max_rows} rows"
                    }
                
                return {
                    "rows": rows,
                    "rowCount": len(rows),
                    "sql": sql
                }
        except Exception as e:
            return {
                "rows": [],
                "rowCount": 0,
                "sql": sql,
                "error": str(e)
            }
