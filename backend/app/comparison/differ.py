import difflib
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import DocumentChunk, DocumentComparison
from app.config import settings
from app.observability.logger import logger

class DocumentDiffer:
    """
    Intelligent Document Version Comparison Engine.
    Detects additions, removals, changed clauses, numerical value alterations,
    and classifies importance/severity.
    """

    def _normalize_text(self, text: str) -> str:
        # Normalize whitespace while preserving content
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_numbers(self, text: str) -> List[str]:
        return re.findall(r'[-+]?\b\d+(?:,\d{3})*(?:\.\d+)?\b%?', text)

    def _classify_significance(self, old_text: str, new_text: str, change_type: str) -> Dict[str, Any]:
        if change_type == "addition":
            return {
                "significance": "medium",
                "reason": "New section or clause introduced into document."
            }
        if change_type == "deletion":
            return {
                "significance": "high" if len(old_text.split()) > 20 else "medium",
                "reason": "Existing clause or content removed from revised version."
            }

        # Check for numerical changes (amounts, dates, percentages)
        old_nums = set(self._extract_numbers(old_text))
        new_nums = set(self._extract_numbers(new_text))
        
        if old_nums != new_nums:
            diff_nums = (old_nums - new_nums) | (new_nums - old_nums)
            return {
                "significance": "critical",
                "reason": f"Numerical values altered: {', '.join(list(diff_nums)[:5])}"
            }

        # Check for legal/obligation keywords
        obligation_words = {"shall", "must", "terminate", "penalty", "indemnity", "warrant", "breach", "liability"}
        words_old = set(old_text.lower().split())
        words_new = set(new_text.lower().split())
        if (words_old & obligation_words) != (words_new & obligation_words):
            return {
                "significance": "high",
                "reason": "Contractual or compliance obligation terms altered."
            }

        # Subtle wording change
        return {
            "significance": "low",
            "reason": "Wording or stylistic modification without major value changes."
        }

    def compare_documents(
        self,
        db: Session,
        base_document_id: str,
        target_document_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        base_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == base_document_id,
            DocumentChunk.workspace_id == workspace_id
        ).order_by(DocumentChunk.page_start, DocumentChunk.id).all()

        target_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == target_document_id,
            DocumentChunk.workspace_id == workspace_id
        ).order_by(DocumentChunk.page_start, DocumentChunk.id).all()

        base_texts = [self._normalize_text(c.content) for c in base_chunks]
        target_texts = [self._normalize_text(c.content) for c in target_chunks]

        matcher = difflib.SequenceMatcher(None, base_texts, target_texts)
        changes = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            if tag == "replace":
                for b_idx, t_idx in zip(range(i1, i2), range(j1, j2)):
                    b_chunk = base_chunks[b_idx]
                    t_chunk = target_chunks[t_idx]
                    classification = self._classify_significance(b_chunk.content, t_chunk.content, "modification")
                    
                    changes.append({
                        "change_type": "modification",
                        "significance": classification["significance"],
                        "explanation": classification["reason"],
                        "old_page": b_chunk.page_start,
                        "new_page": t_chunk.page_start,
                        "section_title": t_chunk.section_title or b_chunk.section_title,
                        "old_text": b_chunk.content,
                        "new_text": t_chunk.content,
                        "old_chunk_id": b_chunk.id,
                        "new_chunk_id": t_chunk.id
                    })
            elif tag == "delete":
                for b_idx in range(i1, i2):
                    b_chunk = base_chunks[b_idx]
                    classification = self._classify_significance(b_chunk.content, "", "deletion")
                    changes.append({
                        "change_type": "deletion",
                        "significance": classification["significance"],
                        "explanation": classification["reason"],
                        "old_page": b_chunk.page_start,
                        "new_page": None,
                        "section_title": b_chunk.section_title,
                        "old_text": b_chunk.content,
                        "new_text": "",
                        "old_chunk_id": b_chunk.id,
                        "new_chunk_id": None
                    })
            elif tag == "insert":
                for t_idx in range(j1, j2):
                    t_chunk = target_chunks[t_idx]
                    classification = self._classify_significance("", t_chunk.content, "addition")
                    changes.append({
                        "change_type": "addition",
                        "significance": classification["significance"],
                        "explanation": classification["reason"],
                        "old_page": None,
                        "new_page": t_chunk.page_start,
                        "section_title": t_chunk.section_title,
                        "old_text": "",
                        "new_text": t_chunk.content,
                        "old_chunk_id": None,
                        "new_chunk_id": t_chunk.id
                    })

        # Summary statistics
        additions_count = sum(1 for c in changes if c["change_type"] == "addition")
        deletions_count = sum(1 for c in changes if c["change_type"] == "deletion")
        modifications_count = sum(1 for c in changes if c["change_type"] == "modification")
        critical_count = sum(1 for c in changes if c["significance"] == "critical")

        summary = (
            f"Compared versions: {len(changes)} total changes identified "
            f"({additions_count} additions, {deletions_count} deletions, {modifications_count} modifications, "
            f"{critical_count} critical value alterations)."
        )

        return {
            "summary": summary,
            "total_changes": len(changes),
            "changes": changes,
            "statistics": {
                "additions": additions_count,
                "deletions": deletions_count,
                "modifications": modifications_count,
                "critical": critical_count
            }
        }

document_differ = DocumentDiffer()
