from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ExtractionRun, Document
from app.auth.security import get_current_user, CurrentUser
from app.auth.permissions import verify_document_access, verify_workspace_access
from app.extraction.structured_extractor import structured_extractor, BUILTIN_SCHEMAS

router = APIRouter(prefix="/extractions", tags=["Structured Extractions"])

class RunExtractionRequest(BaseModel):
    document_id: str
    schema_name: str = "project_proposal"
    custom_schema: Optional[Dict[str, Any]] = None
    workspace_id: str = "default-workspace"

class UpdateExtractionRequest(BaseModel):
    extracted_data: Dict[str, Any]
    review_status: str = "reviewed" # 'reviewed', 'approved'

@router.get("/schemas")
def list_available_schemas():
    return BUILTIN_SCHEMAS

@router.post("", status_code=status.HTTP_201_CREATED)
def start_structured_extraction(
    req: RunExtractionRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = verify_document_access(db, user, req.document_id)

    try:
        result = structured_extractor.extract(
            db, doc.id, req.workspace_id, req.schema_name, req.custom_schema
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    run = ExtractionRun(
        workspace_id=req.workspace_id,
        document_id=doc.id,
        schema_name=result["schema_name"],
        target_schema=result["target_schema"],
        extracted_data=result["extracted_data"],
        field_citations=result["field_citations"],
        review_status="draft"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return {
        "id": run.id,
        "document_id": doc.id,
        "document_title": doc.title,
        "schema_name": run.schema_name,
        "schema_title": result["target_schema"].get("title", run.schema_name),
        "target_schema": run.target_schema,
        "extracted_data": run.extracted_data,
        "field_citations": run.field_citations,
        "validation": result["validation"],
        "review_status": run.review_status
    }

@router.get("/{extraction_id}")
def get_extraction(
    extraction_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(ExtractionRun).filter(ExtractionRun.id == extraction_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Extraction record not found")
    verify_workspace_access(db, user, run.workspace_id)
    doc = db.query(Document).filter(Document.id == run.document_id).first()

    return {
        "id": run.id,
        "document_id": run.document_id,
        "document_title": doc.title if doc else "Document",
        "schema_name": run.schema_name,
        "target_schema": run.target_schema,
        "extracted_data": run.extracted_data,
        "field_citations": run.field_citations,
        "review_status": run.review_status,
        "created_at": run.created_at.isoformat() if run.created_at else None
    }

@router.put("/{extraction_id}")
def update_extraction_review(
    extraction_id: str,
    req: UpdateExtractionRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(ExtractionRun).filter(ExtractionRun.id == extraction_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Extraction record not found")
    verify_workspace_access(db, user, run.workspace_id, required_role="editor")

    run.extracted_data = req.extracted_data
    run.review_status = req.review_status
    db.commit()

    return {"message": "Extraction updated successfully", "review_status": run.review_status}

@router.get("/{extraction_id}/export/csv")
def export_extraction_csv(
    extraction_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(ExtractionRun).filter(ExtractionRun.id == extraction_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Extraction record not found")
    verify_workspace_access(db, user, run.workspace_id)

    csv_data = structured_extractor.export_to_csv(run.extracted_data)
    filename = f"extraction_{run.schema_name}_{run.id[:8]}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
