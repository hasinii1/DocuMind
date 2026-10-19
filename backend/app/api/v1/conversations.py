from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Conversation, Message, Citation, Document
from app.auth.security import get_current_user, CurrentUser, detect_prompt_injection
from app.auth.permissions import verify_workspace_access
from app.retrieval.full_text_search import bm25_searcher
from app.retrieval.vector_search import vector_searcher
from app.retrieval.rank_fusion import rank_fusion
from app.retrieval.reranker import reranker
from app.generation.llm_client import llm_client
from app.citations.validator import citation_validator
from app.observability.logger import logger, log_audit_event

router = APIRouter(prefix="/conversations", tags=["Conversations & Q&A"])

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    workspace_id: str = "default-workspace"

class AskQuestionRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    top_k: int = 5

@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(
    req: CreateConversationRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_workspace_access(db, user, req.workspace_id)
    conv = Conversation(
        workspace_id=req.workspace_id,
        user_id=user.id,
        title=req.title
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title, "workspace_id": conv.workspace_id}

@router.get("")
def list_conversations(
    workspace_id: str = "default-workspace",
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_workspace_access(db, user, workspace_id)
    convs = db.query(Conversation).filter(Conversation.workspace_id == workspace_id).order_by(Conversation.updated_at.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "message_count": len(c.messages)
        }
        for c in convs
    ]

@router.post("/{conversation_id}/messages")
def submit_question(
    conversation_id: str,
    req: AskQuestionRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    verify_workspace_access(db, user, conv.workspace_id)

    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Indirect Prompt Injection check
    injection_term = detect_prompt_injection(question)
    if injection_term:
        log_audit_event("prompt_injection_flag", {"trigger": injection_term, "question": question}, user.id, conv.workspace_id)

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=question
    )
    db.add(user_msg)
    db.commit()

    if injection_term:
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Your query contains instructions that violate security policies. DocuMind processes documents strictly without system prompt overrides.",
            insufficient_evidence=True
        )
        db.add(assistant_msg)
        db.commit()
        return {
            "answer": assistant_msg.content,
            "citations": [],
            "insufficient_evidence": True,
            "security_warning": True
        }

    # 2. Hybrid Search (Keyword + Vector)
    bm25_candidates = bm25_searcher.search(
        db, question, conv.workspace_id, req.document_ids, top_k=15
    )
    vector_candidates = vector_searcher.search(
        db, question, conv.workspace_id, req.document_ids, top_k=15
    )

    # 3. Reciprocal Rank Fusion
    fused_candidates = rank_fusion.fuse(bm25_candidates, vector_candidates, top_k=10)

    # 4. Cross-Encoder Reranker
    reranked_evidence = reranker.rerank(question, fused_candidates, top_n=req.top_k)

    # 5. LLM Grounded Answer Generation
    llm_output = llm_client.generate_grounded_answer(question, reranked_evidence)
    answer_text = llm_output.get("answer", "")
    raw_citations = llm_output.get("citations", [])
    insufficient_evidence = llm_output.get("insufficient_evidence", False)

    # 6. Citation Verification against trusted DB
    validated_citations = citation_validator.validate_citations(
        db, raw_citations, reranked_evidence, conv.workspace_id
    )

    # Enrich citations with document title
    doc_cache = {}
    for c in validated_citations:
        d_id = c["document_id"]
        if d_id not in doc_cache:
            d_obj = db.query(Document).filter(Document.id == d_id).first()
            doc_cache[d_id] = d_obj.title if d_obj else "Document"
        c["document_title"] = doc_cache[d_id]

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=answer_text,
        insufficient_evidence=insufficient_evidence,
        metadata_json={"retrieved_chunks_count": len(reranked_evidence)}
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    # Save citations to DB
    for c in validated_citations:
        db_cit = Citation(
            message_id=assistant_msg.id,
            document_id=c["document_id"],
            chunk_id=c["chunk_id"],
            page_number=c["page_number"],
            quote=c["quote"],
            is_verified=c["is_verified"],
            confidence_score=c["confidence_score"]
        )
        db.add(db_cit)
    db.commit()

    return {
        "message_id": assistant_msg.id,
        "role": "assistant",
        "answer": answer_text,
        "citations": validated_citations,
        "insufficient_evidence": insufficient_evidence,
        "retrieved_evidence": [
            {
                "chunk_id": r["chunk_id"],
                "document_id": r["document_id"],
                "page_start": r["page_start"],
                "page_end": r["page_end"],
                "section_title": r.get("section_title"),
                "element_type": r.get("element_type"),
                "content": r["content"],
                "score": r.get("rerank_score", 0.0)
            }
            for r in reranked_evidence
        ]
    }

@router.get("/{conversation_id}/messages")
def get_conversation_history(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    verify_workspace_access(db, user, conv.workspace_id)

    messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()

    output = []
    for m in messages:
        cits = [
            {
                "id": c.id,
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "page_number": c.page_number,
                "quote": c.quote,
                "is_verified": c.is_verified,
                "confidence_score": c.confidence_score
            }
            for c in m.citations
        ]
        output.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "insufficient_evidence": m.insufficient_evidence,
            "citations": cits,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })

    return output
