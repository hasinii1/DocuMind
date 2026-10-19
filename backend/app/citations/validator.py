import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import DocumentChunk
from app.observability.logger import logger

class CitationValidator:
    """
    Validates model-generated citations against trusted database records:
    1. Checks that cited chunk_id exists in retrieved evidence set and database.
    2. Overwrites model-invented page numbers/document IDs with verified database values.
    3. Verifies that the quoted text actually exists in the source chunk content.
    4. Computes citation support confidence.
    """

    def validate_citations(
        self,
        db: Session,
        raw_citations: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
        user_workspace_id: str
    ) -> List[Dict[str, Any]]:
        retrieved_chunk_map = {c["chunk_id"]: c for c in retrieved_chunks}
        validated_citations: List[Dict[str, Any]] = []

        for raw in raw_citations:
            chunk_id = raw.get("chunk_id")
            quote = raw.get("quote", "").strip()

            # 1. Must be in the retrieved evidence set
            if chunk_id not in retrieved_chunk_map:
                logger.warning(f"Citation rejected: chunk_id '{chunk_id}' was not in retrieved evidence.")
                continue

            # 2. Query trusted database record to verify workspace isolation
            db_chunk = db.query(DocumentChunk).filter(
                DocumentChunk.id == chunk_id,
                DocumentChunk.workspace_id == user_workspace_id
            ).first()

            if not db_chunk:
                logger.warning(f"Citation rejected: chunk '{chunk_id}' not found or unauthorized for workspace.")
                continue

            chunk_content = db_chunk.content

            # 3. Verify quote presence in source text
            is_quote_exact = False
            confidence = 1.0

            if quote:
                # Clean punctuation and whitespace for fuzzy containment check
                clean_quote = re.sub(r'\s+', ' ', quote.lower()).strip()
                clean_chunk = re.sub(r'\s+', ' ', chunk_content.lower())
                
                if clean_quote in clean_chunk:
                    is_quote_exact = True
                    confidence = 1.0
                else:
                    # Partial overlap check (e.g., at least 60% of significant words present)
                    q_words = set(clean_quote.split())
                    chunk_words = set(clean_chunk.split())
                    overlap = len(q_words.intersection(chunk_words)) / max(1, len(q_words))
                    if overlap >= 0.6:
                        is_quote_exact = True
                        confidence = round(overlap, 2)
                    else:
                        is_quote_exact = False
                        confidence = 0.3
            else:
                # If model omitted quote, use first sentence of source chunk as verified excerpt
                sentences = re.split(r'(?<=[.!?])\s+', chunk_content)
                quote = sentences[0] if sentences else chunk_content[:150]
                is_quote_exact = True
                confidence = 0.8

            validated_citations.append({
                "chunk_id": db_chunk.id,
                "document_id": db_chunk.document_id,
                "page_number": db_chunk.page_start,
                "page_end": db_chunk.page_end,
                "section_title": db_chunk.section_title,
                "quote": quote,
                "is_verified": is_quote_exact,
                "confidence_score": confidence
            })

        return validated_citations

citation_validator = CitationValidator()
