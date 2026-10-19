import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Document, DocumentElement, DocumentChunk, ProcessingJob
from app.db.storage import storage_manager
from app.auth.security import get_current_user, CurrentUser
from app.auth.permissions import verify_workspace_access, verify_document_access
from app.ingestion.pdf_extractor import pdf_extractor
from app.ingestion.ocr_extractor import ocr_extractor
from app.ingestion.table_extractor import table_extractor
from app.ingestion.vision_extractor import vision_extractor
from app.chunking.layout_chunker import layout_chunker
from app.embeddings.embedder import embedder
from app.observability.logger import logger, log_audit_event

router = APIRouter(prefix="/documents", tags=["Documents"])

def process_document_pipeline(document_id: str, workspace_id: str, db_factory):
    db: Session = db_factory()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.processing_status = "processing"
        job = db.query(ProcessingJob).filter(ProcessingJob.document_id == document_id).first()
        if job:
            job.status = "processing"
            job.stage = "parsing"
            job.progress_percentage = 20
        db.commit()

        # Step 1: PDF Layout & Text Extraction
        elements, summary = pdf_extractor.extract_document(doc.storage_path, doc.id)
        doc.page_count = summary.get("page_count", 1)
        doc.has_scanned_pages = summary.get("has_scanned_pages", False)

        # Step 2: OCR for scanned pages
        if summary.get("scanned_pages"):
            if job:
                job.stage = "ocr"
                job.progress_percentage = 40
                db.commit()
            ocr_elements = ocr_extractor.process_scanned_pages(doc.storage_path, doc.id, summary["scanned_pages"])
            elements.extend(ocr_elements)

        # Step 3: Table extraction
        if job:
            job.stage = "tables"
            job.progress_percentage = 60
            db.commit()
        table_elements = table_extractor.extract_tables(doc.storage_path, doc.id)
        if table_elements:
            doc.has_tables = True
            elements.extend(table_elements)

        # Save document elements to database
        for el in elements:
            db_el = DocumentElement(
                document_id=doc.id,
                page_number=el["page_number"],
                element_type=el["element_type"],
                content=el["content"],
                source_method=el["source_method"],
                bounding_box=el.get("bounding_box"),
                metadata_json=el.get("metadata", {})
            )
            db.add(db_el)
        db.commit()

        # Step 4: Layout-aware chunking
        if job:
            job.stage = "chunking"
            job.progress_percentage = 75
            db.commit()

        raw_chunks = layout_chunker.chunk_elements(elements, doc.id, workspace_id)

        # Step 5: Embeddings Generation
        if job:
            job.stage = "embedding"
            job.progress_percentage = 85
            db.commit()

        for c in raw_chunks:
            emb_vector = embedder.embed_text(c["content"])
            db_chunk = DocumentChunk(
                document_id=doc.id,
                workspace_id=workspace_id,
                page_start=c["page_start"],
                page_end=c["page_end"],
                section_title=c.get("section_title"),
                element_type=c.get("element_type", "prose"),
                content=c["content"],
                embedding_json=emb_vector,
                embedding_model=embedder.model_name,
                metadata_json=c.get("metadata", {})
            )
            db.add(db_chunk)

        doc.processing_status = "completed"
        if job:
            job.stage = "completed"
            job.status = "completed"
            job.progress_percentage = 100
        db.commit()
        logger.info(f"Pipeline completed successfully for document {document_id}")
    except Exception as e:
        logger.error(f"Processing failed for document {document_id}: {e}")
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.processing_status = "failed"
            doc.error_message = str(e)
        job = db.query(ProcessingJob).filter(ProcessingJob.document_id == document_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
        db.commit()
    finally:
        db.close()

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    parent_document_id: Optional[str] = Form(None),
    workspace_id: str = Form("default-workspace"),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_workspace_access(db, user, workspace_id, required_role="editor")

    # Validate and save file securely
    file_info = await storage_manager.validate_and_save(file, workspace_id)

    # Check for duplicate in workspace
    duplicate = db.query(Document).filter(
        Document.workspace_id == workspace_id,
        Document.checksum == file_info["checksum"]
    ).first()

    if duplicate:
        logger.info(f"Duplicate upload detected: {file_info['checksum']}")
        return {
            "message": "Document already exists in workspace",
            "document": {
                "id": duplicate.id,
                "title": duplicate.title,
                "status": duplicate.processing_status,
                "checksum": duplicate.checksum
            }
        }

    doc = Document(
        workspace_id=workspace_id,
        parent_document_id=parent_document_id,
        title=title or file_info["original_filename"],
        original_filename=file_info["original_filename"],
        mime_type=file_info["mime_type"],
        file_size_bytes=file_info["file_size_bytes"],
        checksum=file_info["checksum"],
        storage_path=file_info["storage_path"],
        processing_status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Create initial job tracker
    job = ProcessingJob(
        document_id=doc.id,
        stage="upload",
        status="processing",
        progress_percentage=10
    )
    db.add(job)
    db.commit()

    log_audit_event("document_upload", {"document_id": doc.id, "title": doc.title}, user.id, workspace_id)

    # Process immediately / in background
    from app.db.session import SessionLocal
    background_tasks.add_task(process_document_pipeline, doc.id, workspace_id, SessionLocal)

    return {
        "message": "Document uploaded successfully. Processing started.",
        "document_id": doc.id,
        "job_id": job.id,
        "title": doc.title,
        "status": doc.processing_status
    }

@router.get("")
def list_documents(
    workspace_id: str = "default-workspace",
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_workspace_access(db, user, workspace_id)
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "original_filename": d.original_filename,
            "mime_type": d.mime_type,
            "file_size_bytes": d.file_size_bytes,
            "page_count": d.page_count,
            "has_tables": d.has_tables,
            "has_scanned_pages": d.has_scanned_pages,
            "processing_status": d.processing_status,
            "parent_document_id": d.parent_document_id,
            "error_message": d.error_message,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]

@router.get("/{document_id}")
def get_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = verify_document_access(db, user, document_id)
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    element_count = db.query(DocumentElement).filter(DocumentElement.document_id == doc.id).count()

    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "title": doc.title,
        "original_filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "page_count": doc.page_count,
        "has_tables": doc.has_tables,
        "has_scanned_pages": doc.has_scanned_pages,
        "processing_status": doc.processing_status,
        "chunk_count": chunk_count,
        "element_count": element_count,
        "parent_document_id": doc.parent_document_id,
        "error_message": doc.error_message,
        "created_at": doc.created_at.isoformat() if doc.created_at else None
    }

@router.get("/{document_id}/download")
def download_document_file(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = verify_document_access(db, user, document_id)
    if not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="File content not found on server disk.")

    return FileResponse(
        path=doc.storage_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.get("/{document_id}/pages/{page_number}")
def get_page_elements(
    document_id: str,
    page_number: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = verify_document_access(db, user, document_id)
    elements = db.query(DocumentElement).filter(
        DocumentElement.document_id == doc.id,
        DocumentElement.page_number == page_number
    ).all()

    return {
        "document_id": doc.id,
        "page_number": page_number,
        "elements": [
            {
                "id": el.id,
                "element_type": el.element_type,
                "content": el.content,
                "bounding_box": el.bounding_box,
                "source_method": el.source_method,
                "metadata": el.metadata_json
            }
            for el in elements
        ]
    }

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = verify_document_access(db, user, document_id)
    verify_workspace_access(db, user, doc.workspace_id, required_role="admin")

    storage_path = doc.storage_path
    db.delete(doc)
    db.commit()

    storage_manager.delete_file(storage_path)
    log_audit_event("document_delete", {"document_id": document_id}, user.id, doc.workspace_id)

    return {"message": "Document and all associated chunks/citations deleted successfully."}
