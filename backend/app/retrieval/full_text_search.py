import re
import math
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from app.db.models import DocumentChunk
from app.observability.logger import logger

class BM25Searcher:
    """
    BM25 Keyword search implementation for exact terminology, numbers, dates, and names.
    Supports in-memory scoring over filtered workspace/document chunks.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def search(
        self,
        db: Session,
        query: str,
        workspace_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        # Query candidate chunks matching workspace and document filters
        q = db.query(DocumentChunk).filter(DocumentChunk.workspace_id == workspace_id)
        if document_ids:
            q = q.filter(DocumentChunk.document_id.in_(document_ids))
        
        chunks = q.all()
        if not chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Corpus stats
        corpus_size = len(chunks)
        doc_lengths = []
        tokenized_docs = []
        doc_freqs = Counter()

        for chunk in chunks:
            tokens = self._tokenize(chunk.content)
            tokenized_docs.append(tokens)
            doc_lengths.append(len(tokens))
            unique_tokens = set(tokens)
            for t in unique_tokens:
                doc_freqs[t] += 1

        avg_doc_len = sum(doc_lengths) / max(1, corpus_size)

        scored_results = []
        for i, chunk in enumerate(chunks):
            tokens = tokenized_docs[i]
            doc_len = doc_lengths[i]
            tf = Counter(tokens)
            score = 0.0

            for q_term in query_tokens:
                if q_term not in tf:
                    continue
                # Term IDF
                df = doc_freqs.get(q_term, 0)
                idf = math.log(1.0 + (corpus_size - df + 0.5) / (df + 0.5))
                
                # BM25 TF formula
                f = tf[q_term]
                num = f * (self.k1 + 1)
                den = f + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_doc_len))
                score += idf * (num / den)

            if score > 0:
                scored_results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section_title": chunk.section_title,
                    "element_type": chunk.element_type,
                    "content": chunk.content,
                    "metadata": chunk.metadata_json,
                    "bm25_score": round(score, 4)
                })

        scored_results.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_results[:top_k]

bm25_searcher = BM25Searcher()
