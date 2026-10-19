from typing import List, Dict, Any

class ReciprocalRankFusion:
    """
    Combines ranked result lists from Keyword (BM25) and Semantic (Vector) search
    using standard Reciprocal Rank Fusion (RRF):
    RRF(d) = sum(1 / (k + rank_r(d)))
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        keyword_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        scores: Dict[str, float] = {}
        items: Dict[str, Dict[str, Any]] = {}

        # Process keyword rankings
        for rank, item in enumerate(keyword_results):
            cid = item["chunk_id"]
            rrf_score = 1.0 / (self.k + (rank + 1))
            scores[cid] = scores.get(cid, 0.0) + rrf_score
            if cid not in items:
                items[cid] = item.copy()
            items[cid]["bm25_rank"] = rank + 1

        # Process vector rankings
        for rank, item in enumerate(vector_results):
            cid = item["chunk_id"]
            rrf_score = 1.0 / (self.k + (rank + 1))
            scores[cid] = scores.get(cid, 0.0) + rrf_score
            if cid not in items:
                items[cid] = item.copy()
            items[cid]["vector_rank"] = rank + 1

        fused = []
        for cid, rrf_score in scores.items():
            entry = items[cid]
            entry["rrf_score"] = round(rrf_score, 6)
            fused.append(entry)

        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused[:top_k]

rank_fusion = ReciprocalRankFusion()
