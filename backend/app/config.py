import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "documind_secret_development_key_change_in_production"
    
    # Server
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./documind.db"
    USE_PGVECTOR: bool = False
    
    # Supabase (optional)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_BUCKET_NAME: str = "documind-documents"
    
    # Storage
    LOCAL_STORAGE_DIR: str = "./storage/uploads"
    
    # LLM & AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Embeddings
    EMBEDDING_PROVIDER: str = "local" # 'sentence-transformers', 'gemini', or 'local'
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Reranking
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ENABLE_RERANKER: bool = True
    
    # Processing Limits
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_PAGES_PER_DOCUMENT: int = 200
    DEFAULT_CHUNK_SIZE_TOKENS: int = 600
    DEFAULT_CHUNK_OVERLAP_TOKENS: int = 100

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
