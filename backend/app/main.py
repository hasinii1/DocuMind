import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import init_db
from app.api.v1 import api_v1_router
from app.observability.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing DocuMind AI Backend...")
    init_db()
    logger.info(f"DocuMind ready on {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    yield
    logger.info("DocuMind AI Backend shutting down.")

app = FastAPI(
    title="DocuMind AI - Document Intelligence Platform",
    description="Multimodal document intelligence with verified source citations, version diffing, and structured extraction.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Root route
@app.get("/")
def read_root():
    return {
        "project": "DocuMind AI",
        "description": "Full-Stack Multimodal Document Intelligence Platform",
        "docs_url": "/docs",
        "api_v1": "/api/v1"
    }

# Mount Versioned API
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
