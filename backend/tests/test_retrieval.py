import pytest
from app.retrieval.rank_fusion import ReciprocalRankFusion

def test_reciprocal_rank_fusion_scoring():
    rrf = ReciprocalRankFusion(k=60)

    keyword_results = [
        {"chunk_id": "c1", "content": "Operating expenses"},
        {"chunk_id": "c2", "content": "Revenue targets"}
    ]
    vector_results = [
        {"chunk_id": "c2", "content": "Revenue targets"},
        {"chunk_id": "c3", "content": "Engineering compensation"}
    ]

    fused = rrf.fuse(keyword_results, vector_results, top_k=5)
    assert len(fused) == 3

    # c2 appeared in both rankings (rank 2 and rank 1), should have highest fused score:
    # 1/(60+2) + 1/(60+1) = 0.016129 + 0.016393 = ~0.0325
    assert fused[0]["chunk_id"] == "c2"
    assert fused[0]["rrf_score"] > fused[1]["rrf_score"]
