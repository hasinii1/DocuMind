from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import DocumentComparison, Document
from app.auth.security import get_current_user, CurrentUser
from app.auth.permissions import verify_document_access, verify_workspace_access
from app.comparison.differ import document_differ

router = APIRouter(prefix="/comparisons", tags=["Document Comparisons"])

class CreateComparisonRequest(BaseModel):
    base_document_id: str
    target_document_id: str
    workspace_id: str = "default-workspace"

@router.post("", status_code=status.HTTP_201_CREATED)
def compare_document_versions(
    req: CreateComparisonRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    base_doc = verify_document_access(db, user, req.base_document_id)
    target_doc = verify_document_access(db, user, req.target_document_id)

    diff_result = document_differ.compare_documents(
        db, base_doc.id, target_doc.id, req.workspace_id
    )

    comparison = DocumentComparison(
        workspace_id=req.workspace_id,
        base_document_id=base_doc.id,
        target_document_id=target_doc.id,
        summary=diff_result["summary"],
        changes_json=diff_result["changes"],
        status="completed"
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)

    return {
        "id": comparison.id,
        "base_document": {"id": base_doc.id, "title": base_doc.title},
        "target_document": {"id": target_doc.id, "title": target_doc.title},
        "summary": comparison.summary,
        "statistics": diff_result["statistics"],
        "changes": comparison.changes_json
    }

@router.get("")
def list_comparisons(
    workspace_id: str = "default-workspace",
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_workspace_access(db, user, workspace_id)
    comps = db.query(DocumentComparison).filter(DocumentComparison.workspace_id == workspace_id).order_by(DocumentComparison.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "base_document_id": c.base_document_id,
            "target_document_id": c.target_document_id,
            "summary": c.summary,
            "status": c.status,
            "changes_count": len(c.changes_json) if c.changes_json else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in comps
    ]

@router.get("/{comparison_id}")
def get_comparison(
    comparison_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comp = db.query(DocumentComparison).filter(DocumentComparison.id == comparison_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison run not found")
    verify_workspace_access(db, user, comp.workspace_id)

    base_doc = db.query(Document).filter(Document.id == comp.base_document_id).first()
    target_doc = db.query(Document).filter(Document.id == comp.target_document_id).first()

    return {
        "id": comp.id,
        "base_document": {"id": base_doc.id, "title": base_doc.title} if base_doc else None,
        "target_document": {"id": target_doc.id, "title": target_doc.title} if target_doc else None,
        "summary": comp.summary,
        "status": comp.status,
        "changes": comp.changes_json,
        "created_at": comp.created_at.isoformat() if comp.created_at else None
    }
