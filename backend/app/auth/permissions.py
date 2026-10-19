from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models import Workspace, WorkspaceMember, Document
from app.auth.security import CurrentUser

def verify_workspace_access(db: Session, user: CurrentUser, workspace_id: str, required_role: str = "viewer"):
    if user.role == "admin" or workspace_id == "default-workspace":
        return True

    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to workspace '{workspace_id}'."
        )

    roles_hierarchy = ["viewer", "editor", "admin", "owner"]
    try:
        user_level = roles_hierarchy.index(member.role)
        required_level = roles_hierarchy.index(required_role)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {required_role} role."
            )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role.")

    return True

def verify_document_access(db: Session, user: CurrentUser, document_id: str) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    verify_workspace_access(db, user, doc.workspace_id)
    return doc
