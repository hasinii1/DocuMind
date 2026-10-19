from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ProcessingJob, Document
from app.auth.security import get_current_user, CurrentUser

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

@router.get("/{job_id}")
def get_job_status(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    doc = db.query(Document).filter(Document.id == job.document_id).first()

    return {
        "job_id": job.id,
        "document_id": job.document_id,
        "document_title": doc.title if doc else None,
        "stage": job.stage,
        "status": job.status,
        "progress_percentage": job.progress_percentage,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None
    }
