from fastapi import APIRouter
from datetime import datetime, timezone
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "DocuMind AI Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": settings.DATABASE_URL.split("://")[0],
        "reranker_enabled": settings.ENABLE_RERANKER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
