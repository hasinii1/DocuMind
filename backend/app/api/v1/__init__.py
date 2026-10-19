from fastapi import APIRouter
from .health import router as health_router
from .documents import router as documents_router
from .conversations import router as conversations_router
from .comparisons import router as comparisons_router
from .extractions import router as extractions_router
from .jobs import router as jobs_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(comparisons_router)
api_v1_router.include_router(extractions_router)
api_v1_router.include_router(jobs_router)

__all__ = ["api_v1_router"]
