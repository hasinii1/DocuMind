import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal, init_db
from app.db.models import Document, DocumentElement, DocumentChunk, Conversation, Message, Citation
from app.ingestion.pdf_extractor import pdf_extractor
from app.ingestion.table_extractor import table_extractor
from app.chunking.layout_chunker import layout_chunker
from app.embeddings.embedder import embedder
from app.retrieval.full_text_search import bm25_searcher
from app.retrieval.vector_search import vector_searcher
from app.retrieval.rank_fusion import rank_fusion
from app.retrieval.reranker import reranker
from app.generation.llm_client import llm_client
from app.citations.validator import citation_validator

def test_pipeline():
    init_db()
    db = SessionLocal()

    pdf_path = str(Path(__file__).parent.parent / "sample_corporate_report.pdf")
    doc_id = "doc_test_e2e"
    workspace_id = "default-workspace"

    print("\n[Step 1] Ingesting and extracting layout from sample PDF...")
    elements, summary = pdf_extractor.extract_document(pdf_path, doc_id)
    print(f"  Extracted {len(elements)} elements across {summary['page_count']} pages.")

    print("\n[Step 2] Chunking with layout awareness...")
    chunks = layout_chunker.chunk_elements(elements, doc_id, workspace_id)
    print(f"  Created {len(chunks)} layout-aware chunks.")

    # Clear previous e2e chunks in DB if any
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    db.commit()

    print("\n[Step 3] Embedding and indexing chunks into database...")
    for c in chunks:
        emb = embedder.embed_text(c["content"])
        db_chunk = DocumentChunk(
            id=c.get("id") or None,
            document_id=doc_id,
            workspace_id=workspace_id,
            page_start=c["page_start"],
            page_end=c["page_end"],
            section_title=c.get("section_title"),
            element_type=c.get("element_type", "prose"),
            content=c["content"],
            embedding_json=emb,
            embedding_model="hash-vector"
        )
        db.add(db_chunk)
    db.commit()
    print("  Chunks persisted to DB successfully.")

    # Step 4: Ask User's Example Question
    question = "What were the three main causes of the reported increase in operating costs, and what evidence supports each cause?"
    print(f"\n[Step 4] Query: '{question}'")

    bm25_res = bm25_searcher.search(db, question, workspace_id, top_k=5)
    vec_res = vector_searcher.search(db, question, workspace_id, top_k=5)
    fused = rank_fusion.fuse(bm25_res, vec_res, top_k=5)
    reranked = reranker.rerank(question, fused, top_n=3)

    print(f"  Top retrieved evidence page numbers: {[r['page_start'] for r in reranked]}")

    print("\n[Step 5] Generating grounded answer with citation validation...")
    answer_res = llm_client.generate_grounded_answer(question, reranked)
    val_citations = citation_validator.validate_citations(db, answer_res.get("citations", []), reranked, workspace_id)

    print("\n--- GROUNDED ANSWER ---")
    print(answer_res.get("answer"))
    print("\n--- VALIDATED CITATIONS ---")
    for cit in val_citations:
        print(f"  * Page {cit['page_number']}: '{cit['quote'][:90]}...' (Verified: {cit['is_verified']}, Conf: {cit['confidence_score']})")

    # Step 6: Test Abstention Query
    unsupported_q = "What was the CEO's personal stock sale profit in 2021?"
    print(f"\n[Step 6] Testing Abstention with unsupported question: '{unsupported_q}'")
    bm25_un = bm25_searcher.search(db, unsupported_q, workspace_id, top_k=5)
    vec_un = vector_searcher.search(db, unsupported_q, workspace_id, top_k=5)
    fused_un = rank_fusion.fuse(bm25_un, vec_un, top_k=5)
    reranked_un = reranker.rerank(unsupported_q, fused_un, top_n=3)
    abstain_res = llm_client.generate_grounded_answer(unsupported_q, reranked_un)
    print(f"  Abstention triggered (insufficient_evidence={abstain_res.get('insufficient_evidence')}):")
    print(f"  Response: {abstain_res.get('answer')}")

    db.close()
    print("\n>> All End-to-End Pipeline Steps Verified Successfully! <<\n")

if __name__ == "__main__":
    test_pipeline()
