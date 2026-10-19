import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import DocumentChunk
from app.embeddings.embedder import embedder
from app.observability.logger import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

class VectorSearcher:
    """
    Semantic vector search over embedded document chunks.
    """

    def search(
        self,
        db: Session,
        query: str,
        workspace_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        query_vector = embedder.embed_query(query)

        q = db.query(DocumentChunk).filter(DocumentChunk.workspace_id == workspace_id)
        if document_ids:
            q = q.filter(DocumentChunk.document_id.in_(document_ids))

        chunks = q.all()
        if not chunks:
            return []

        scored_results = []
        for chunk in chunks:
            if not chunk.embedding_json:
                continue
            sim = cosine_similarity(query_vector, chunk.embedding_json)
            scored_results.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "section_title": chunk.section_title,
                "element_type": chunk.element_type,
                "content": chunk.content,
                "metadata": chunk.metadata_json,
                "vector_score": round(sim, 4)
            })

        scored_results.sort(key=lambda x: x["vector_score"], reverse=True)
        return scored_results[:top_k]

vector_searcher = VectorSearcher()
