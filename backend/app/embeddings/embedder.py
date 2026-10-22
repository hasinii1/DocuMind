import numpy as np
from typing import List
from google import genai
from google.genai import types
from app.config import settings
from app.observability.logger import logger


class DocumentEmbedder:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self._client = None

    def _get_client(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is missing.")
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _embed(self, text: str, task_type: str) -> List[float]:
        if self.provider != "gemini":
            raise RuntimeError(f"Unsupported embedding provider: {self.provider}")
        try:
            response = self._get_client().models.embed_content(
                model=self.model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimension,
                ),
            )
            if not response.embeddings or not response.embeddings[0].values:
                raise RuntimeError("Gemini returned an empty embedding.")
            vector = [float(x) for x in response.embeddings[0].values]
            if len(vector) != self.dimension or not np.isfinite(vector).all():
                raise RuntimeError(f"Invalid embedding vector; dimension={len(vector)}")
            return vector
        except Exception as exc:
            logger.error(f"Gemini {task_type} embedding failed: {exc}")
            raise RuntimeError(f"Gemini embedding failed: {exc}") from exc

    def embed_text(self, text: str) -> List[float]:
        return self._embed(text, "RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> List[float]:
        return self._embed(query, "RETRIEVAL_QUERY")


embedder = DocumentEmbedder()
