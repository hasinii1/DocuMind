import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    BigInteger,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="member")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    workspaces = relationship("Workspace", back_populates="owner")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("Profile", back_populates="workspaces")
    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="viewer") # 'owner', 'admin', 'editor', 'viewer'
    created_at = Column(DateTime, default=utc_now)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False, index=True)
    storage_path = Column(Text, nullable=False)
    processing_status = Column(String(50), default="pending") # 'pending', 'processing', 'completed', 'failed'
    page_count = Column(Integer, default=0)
    has_tables = Column(Boolean, default=False)
    has_scanned_pages = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    workspace = relationship("Workspace", back_populates="documents")
    elements = relationship("DocumentElement", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")

class DocumentElement(Base):
    __tablename__ = "document_elements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    element_type = Column(String(50), nullable=False) # 'paragraph', 'heading', 'table', 'figure', 'ocr_text'
    content = Column(Text, nullable=False)
    source_method = Column(String(100), nullable=False) # 'pdf_text_extractor', 'tesseract_ocr', 'table_extractor', 'vision_model'
    bounding_box = Column(JSON, nullable=True) # { x0, y0, x1, y1 }
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    document = relationship("Document", back_populates="elements")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    section_title = Column(String(255), nullable=True)
    element_type = Column(String(50), default="prose")
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True) # vector as float array for cross-DB compatibility
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    document = relationship("Document", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    workspace = relationship("Workspace", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False) # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    insufficient_evidence = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")

class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True)
    page_number = Column(Integer, nullable=False)
    quote = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=True)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=utc_now)

    message = relationship("Message", back_populates="citations")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(100), default="upload") # 'upload', 'parsing', 'ocr', 'chunking', 'embedding', 'completed'
    status = Column(String(50), default="pending") # 'pending', 'processing', 'completed', 'failed'
    progress_percentage = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    document = relationship("Document", back_populates="jobs")

class DocumentComparison(Base):
    __tablename__ = "document_comparisons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    base_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    target_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)
    changes_json = Column(JSON, default=list) # [{ type, old_text, new_text, significance, old_page, new_page, old_chunk_id, new_chunk_id }]
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=utc_now)

class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    schema_name = Column(String(100), nullable=False)
    target_schema = Column(JSON, nullable=False)
    extracted_data = Column(JSON, nullable=False)
    field_citations = Column(JSON, default=dict)
    review_status = Column(String(50), default="draft") # 'draft', 'reviewed', 'approved'
    created_at = Column(DateTime, default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=True)
    event_type = Column(String(100), nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
