"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class DatabaseConnector(Base):
    __tablename__ = 'db_connectors'

    connector_id = Column(Integer, primary_key=True)
    tenant_id = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    db_type = Column(Text, nullable=False)
    connection_string = Column(Text, nullable=False)  # Will be encrypted
    schema_info = Column(JSON)
    status = Column(Text, default='active')
    read_only = Column(Boolean, default=True)
    max_rows_per_query = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_schema_sync = Column(DateTime(timezone=True))


class APIConnector(Base):
    __tablename__ = 'api_connectors'

    connector_id = Column(Integer, primary_key=True)
    tenant_id = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    base_url = Column(Text, nullable=False)
    openapi_spec = Column(JSON, nullable=False)
    auth_type = Column(Text)
    auth_config = Column(JSON)
    status = Column(Text, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentSource(Base):
    __tablename__ = 'document_sources'

    source_id = Column(Integer, primary_key=True)
    tenant_id = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    source_type = Column(Text, nullable=False)
    config = Column(JSON, nullable=False)
    file_filters = Column(JSON)
    status = Column(Text, default='active')
    auto_sync = Column(Boolean, default=False)
    sync_schedule = Column(Text)
    last_sync_at = Column(DateTime(timezone=True))
    files_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WebConnector(Base):
    __tablename__ = 'web_connectors'

    connector_id = Column(Integer, primary_key=True)
    tenant_id = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    connector_type = Column(Text, nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(Text, default='active')
    rate_limit_config = Column(JSON)
    cache_config = Column(JSON)
    auth_config = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True))

