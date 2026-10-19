import hashlib
import numpy as np
from typing import List, Optional
from app.config import settings
from app.observability.logger import logger

class DocumentEmbedder:
    """
    Modular embedding generator supporting:
    1. Google Gemini Embeddings (API)
    2. Sentence-Transformers (Local Neural)
    3. Hashing/TF-IDF Vectorizer (Deterministic local fallback)
    """

    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self._st_model = None

    def _get_st_model(self):
        if self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({self.model_name}): {e}")
                self._st_model = False
        return self._st_model

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Fast deterministic hash-based embedding into fixed dimension.
        Ensures consistent, reproducible vector search without external models.
        """
        words = text.lower().split()
        vec = np.zeros(self.dimension, dtype=np.float32)
        if not words:
            return vec.tolist()

        for word in words:
            # Deterministic hash bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return [round(float(x), 5) for x in vec.tolist()]

    def embed_text(self, text: str) -> List[float]:
        # Try Gemini API if key is set and requested
        if self.provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document"
                )
                if "embedding" in res:
                    return res["embedding"]
            except Exception as e:
                logger.error(f"Gemini embedding call failed: {e}")

        # Try SentenceTransformers if available
        st = self._get_st_model()
        if st and st is not False:
            try:
                emb = st.encode(text, convert_to_numpy=True)
                return [round(float(x), 5) for x in emb.tolist()]
            except Exception as e:
                logger.error(f"SentenceTransformer embedding failed: {e}")

        # Fallback
        return self._fallback_embed(text)

    def embed_query(self, query: str) -> List[float]:
        if self.provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=query,
                    task_type="retrieval_query"
                )
                if "embedding" in res:
                    return res["embedding"]
            except Exception as e:
                logger.error(f"Gemini query embedding failed: {e}")

        st = self._get_st_model()
        if st and st is not False:
            try:
                emb = st.encode(query, convert_to_numpy=True)
                return [round(float(x), 5) for x in emb.tolist()]
            except Exception as e:
                logger.error(f"SentenceTransformer query embedding failed: {e}")

        return self._fallback_embed(query)

embedder = DocumentEmbedder()
