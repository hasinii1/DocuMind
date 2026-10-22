import json
import os
import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal, init_db
from app.db.models import Document, DocumentChunk, Workspace
from app.retrieval.full_text_search import bm25_searcher
from app.retrieval.vector_search import vector_searcher
from app.retrieval.rank_fusion import rank_fusion
from app.retrieval.reranker import reranker
from app.generation.llm_client import llm_client
from app.citations.validator import citation_validator
from app.auth.security import detect_prompt_injection

def seed_benchmark_documents(db: SessionLocal):
    doc_id = "bench_doc_100"
    existing = db.query(Document).filter(Document.id == doc_id).first()
    if not existing:
        doc = Document(
            id=doc_id,
            workspace_id="default-workspace",
            title="Q3 Corporate Financial & Engineering Report",
            original_filename="q3_corporate_report.pdf",
            mime_type="application/pdf",
            file_size_bytes=45000,
            checksum="bench_checksum_q3_report",
            storage_path="./storage/uploads/bench_mock.pdf",
            processing_status="completed",
            page_count=5,
            has_tables=True
        )
        db.add(doc)

        chunks_data = [
            (1, "Executive Summary", "Project DocuMind is designed for document intelligence, producing grounded answers with clickable source citations and verification."),
            (2, "Milestones & Delivery", "Milestone 4 delivery in Q4 directly incorporates the revised SOC2 and quarterly compliance penetration testing criteria."),
            (3, "Financial Overview & Costs", "The three main causes of the reported increase in operating costs were cloud infrastructure expansion, third-party licensing fees, and specialized engineering headcount growth."),
            (4, "Financial Summary Table", "| Metric | Q1 | Q2 | Q3 |\n| --- | --- | --- |\n| Total Revenue | $1.2M | $1.35M | $1,450,000 |\n| Operating Costs | $450K | $520K | $680K |"),
            (5, "Security Audit Criteria", "All quarterly compliance audits must satisfy SOC2 Type II requirements and penetration testing prior to deployment."),
            (2, "Contract Terminations", "Under Version 2, contract cancellation requires 60 days written notice with a penalty clause, updating the earlier 30 days notice rule.")
        ]

        from app.embeddings.embedder import embedder
        for idx, (p, sec, txt) in enumerate(chunks_data):
            emb = embedder.embed_text(txt)
            c = DocumentChunk(
                id=f"bench_chunk_{idx+1}",
                document_id=doc_id,
                workspace_id="default-workspace",
                page_start=p,
                page_end=p,
                section_title=sec,
                element_type="table" if "|" in txt else "prose",
                content=txt,
                embedding_json=emb,
                embedding_model="hash-fallback"
            )
            db.add(c)
        db.commit()

def configure_offline_benchmark_embeddings():
    """Use deterministic local embeddings for CI; production stays on Gemini."""
    import hashlib
    import math
    import re
    from app.embeddings.embedder import embedder
    from app.config import settings

    dimension = settings.EMBEDDING_DIMENSION

    def local_embedding(text):
        vector = [0.0] * dimension
        tokens = re.findall(r"[a-z0-9]+", text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    # Patch the shared embedder used by both document seeding and vector search.
    embedder.embed_text = local_embedding
    embedder.embed_query = local_embedding


def run_benchmark():
    if os.getenv("DOCUMIND_OFFLINE_EVALUATION", "").lower() == "true":
        configure_offline_benchmark_embeddings()
    init_db()
    db = SessionLocal()
    seed_benchmark_documents(db)
    dataset_path = Path(__file__).parent / "datasets" / "benchmark_eval.json"
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    test_cases = bench_data.get("test_cases", [])
    workspace_id = "default-workspace"

    print(f"\n=======================================================")
    print(f"  DocuMind Evaluation Benchmark: {bench_data['benchmark_name']}")
    print(f"=======================================================\n")

    results = []
    total_latency = 0.0
    recall_at_5_hits = 0
    mrr_total = 0.0
    valid_citations_count = 0
    total_citations_count = 0
    correct_abstentions = 0
    total_abstention_cases = 0

    for tc in test_cases:
        qid = tc["id"]
        q_text = tc["question"]
        expected_pages = set(tc["expected_pages"])
        requires_abstention = tc["requires_abstention"]

        t0 = time.time()

        # Step 1: Security injection check
        injection_flag = detect_prompt_injection(q_text)

        # Step 2: Hybrid Retrieval
        bm25_res = bm25_searcher.search(db, q_text, workspace_id, top_k=10)
        vec_res = vector_searcher.search(db, q_text, workspace_id, top_k=10)
        fused = rank_fusion.fuse(bm25_res, vec_res, top_k=10)
        reranked = reranker.rerank(q_text, fused, top_n=5)

        # Step 3: Evaluate Retrieval Recall and MRR
        retrieved_pages = [r.get("page_start") for r in reranked]
        hit = False
        rr = 0.0
        for rank, p in enumerate(retrieved_pages, 1):
            if p in expected_pages:
                hit = True
                if rr == 0.0:
                    rr = 1.0 / rank

        if expected_pages:
            if hit:
                recall_at_5_hits += 1
            mrr_total += rr

        # Step 4: Generation & Citation Validation
        if injection_flag:
            gen_res = {
                "answer": "Request rejected due to untrusted instruction detection.",
                "citations": [],
                "insufficient_evidence": True
            }
        elif os.getenv("DOCUMIND_OFFLINE_EVALUATION", "").lower() == "true":
            gen_res = {
                "answer": "Offline CI mode: live generation skipped.",
                "citations": [],
                "insufficient_evidence": False,
            }
        else:
            gen_res = llm_client.generate_grounded_answer(q_text, reranked)

        val_citations = citation_validator.validate_citations(
            db,
            gen_res.get("citations", []),
            reranked,
            workspace_id
        )

        latency = time.time() - t0
        total_latency += latency

        # Evaluate citations
        for c in val_citations:
            total_citations_count += 1
            if c["is_verified"] and c["confidence_score"] >= 0.7:
                valid_citations_count += 1

        # Evaluate abstention
        is_abstained = gen_res.get("insufficient_evidence", False) or injection_flag is not None
        if requires_abstention:
            total_abstention_cases += 1
            if is_abstained:
                correct_abstentions += 1

        status_str = "PASS" if (requires_abstention and is_abstained) or (not requires_abstention and hit) else "REVIEW"
        print(f"[{status_str}] {qid:25} | Latency: {latency:.3f}s | Abstained: {is_abstained} | Hits: {retrieved_pages}")

        results.append({
            "test_id": qid,
            "question": q_text,
            "status": status_str,
            "latency_seconds": round(latency, 3),
            "retrieved_pages": retrieved_pages,
            "answer_preview": gen_res.get("answer", "")[:100] + "...",
            "citations_returned": len(val_citations),
            "insufficient_evidence": is_abstained
        })

    eval_cases_factual = len(test_cases) - total_abstention_cases
    recall_rate = (recall_at_5_hits / max(1, eval_cases_factual)) * 100
    mrr_score = mrr_total / max(1, eval_cases_factual)
    offline_mode = os.getenv("DOCUMIND_OFFLINE_EVALUATION", "").lower() == "true"
    citation_precision = None if offline_mode else (
        (valid_citations_count / max(1, total_citations_count)) * 100
        if total_citations_count else 100.0
    )
    abstention_accuracy = None if offline_mode else (
        (correct_abstentions / max(1, total_abstention_cases)) * 100
        if total_abstention_cases else 100.0
    )
    avg_latency = total_latency / max(1, len(test_cases))

    metrics = {
        "benchmark": bench_data["benchmark_name"],
        "total_test_cases": len(test_cases),
        "recall_at_5_percentage": round(recall_rate, 2),
        "mrr": round(mrr_score, 4),
        "citation_validity_percentage": round(citation_precision, 2) if citation_precision is not None else None,
        "abstention_accuracy_percentage": round(abstention_accuracy, 2) if abstention_accuracy is not None else None,
        "average_latency_seconds": round(avg_latency, 3)
    }

    print("\n-------------------------------------------------------")
    print(f"BENCHMARK SUMMARY RESULTS:")
    print(f"  Recall@5:              {metrics['recall_at_5_percentage']}%")
    print(f"  Mean Reciprocal Rank:  {metrics['mrr']}")
    print(f"  Citation Validity:     {metrics['citation_validity_percentage']}%")
    print(f"  Abstention Precision:  {metrics['abstention_accuracy_percentage']}%")
    print(f"  Average Latency:       {metrics['average_latency_seconds']}s")
    print("-------------------------------------------------------\n")

    # Output report JSON
    report_path = Path(__file__).parent / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "detailed_results": results}, f, indent=2)

    db.close()
    return metrics

if __name__ == "__main__":
    run_benchmark()
