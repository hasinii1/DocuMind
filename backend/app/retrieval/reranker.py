from typing import List, Dict, Any
from app.config import settings
from app.observability.logger import logger

class CrossEncoderReranker:
    """
    Reranks question-chunk candidate pairs to maximize evidence relevance.
    """

    def __init__(self):
        self.enabled = settings.ENABLE_RERANKER
        self.model_name = settings.RERANKER_MODEL_NAME
        self._cross_encoder = None

    def _get_cross_encoder(self):
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                self._cross_encoder = CrossEncoder(self.model_name)
            except Exception as e:
                logger.info(f"CrossEncoder not initialized (using lexical-semantic scoring): {e}")
                self._cross_encoder = False
        return self._cross_encoder

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        # If CrossEncoder is available
        ce = self._get_cross_encoder()
        if ce and ce is not False:
            try:
                pairs = [[query, c["content"]] for c in candidates]
                scores = ce.predict(pairs)
                for i, c in enumerate(candidates):
                    c["rerank_score"] = float(scores[i])
                candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
                return candidates[:top_n]
            except Exception as e:
                logger.error(f"Error in CrossEncoder inference: {e}")

        # High-precision fallback scoring based on query term coverage and RRF rank
        q_words = set(query.lower().split())
        for c in candidates:
            c_text = c["content"].lower()
            matches = sum(1 for w in q_words if w in c_text)
            term_coverage = matches / max(1, len(q_words))
            rrf = c.get("rrf_score", 0.0)
            c["rerank_score"] = round(term_coverage * 0.6 + rrf * 40.0, 4)

        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_n]

reranker = CrossEncoderReranker()
