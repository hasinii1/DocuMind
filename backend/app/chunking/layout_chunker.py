import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.observability.logger import logger

class LayoutAwareChunker:
    """
    Layout-aware text chunking that preserves:
    - Section headings paired with corresponding body text
    - Tables kept intact with their header rows
    - Element types and precise page boundaries
    - Configurable token budgets and sliding overlap
    """

    def __init__(
        self,
        target_chunk_size: int = settings.DEFAULT_CHUNK_SIZE_TOKENS,
        overlap_size: int = settings.DEFAULT_CHUNK_OVERLAP_TOKENS
    ):
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

    def _approx_token_count(self, text: str) -> int:
        # 1 word ~ 1.3 tokens
        return int(len(text.split()) * 1.3)

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split on sentence boundaries preserving abbreviations where feasible
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_elements(
        self,
        elements: List[Dict[str, Any]],
        document_id: str,
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        current_section = "Introduction / Overview"
        prose_buffer: List[str] = []
        page_start = None
        page_end = None

        def flush_prose_buffer():
            nonlocal prose_buffer, page_start, page_end, current_section
            if not prose_buffer:
                return

            full_text = " ".join(prose_buffer)
            sentences = self._split_into_sentences(full_text)
            
            chunk_sentences = []
            current_tokens = 0

            for sentence in sentences:
                sent_tokens = self._approx_token_count(sentence)
                if current_tokens + sent_tokens > self.target_chunk_size and chunk_sentences:
                    chunk_text = " ".join(chunk_sentences)
                    chunks.append({
                        "document_id": document_id,
                        "workspace_id": workspace_id,
                        "page_start": page_start or 1,
                        "page_end": page_end or page_start or 1,
                        "section_title": current_section,
                        "element_type": "prose",
                        "content": chunk_text,
                        "metadata": {
                            "token_count": self._approx_token_count(chunk_text),
                            "sentence_count": len(chunk_sentences)
                        }
                    })
                    
                    # Sliding window overlap
                    overlap_sentences = []
                    overlap_tokens = 0
                    for s in reversed(chunk_sentences):
                        st = self._approx_token_count(s)
                        if overlap_tokens + st <= self.overlap_size:
                            overlap_sentences.insert(0, s)
                            overlap_tokens += st
                        else:
                            break
                    chunk_sentences = overlap_sentences + [sentence]
                    current_tokens = overlap_tokens + sent_tokens
                else:
                    chunk_sentences.append(sentence)
                    current_tokens += sent_tokens

            if chunk_sentences:
                chunk_text = " ".join(chunk_sentences)
                chunks.append({
                    "document_id": document_id,
                    "workspace_id": workspace_id,
                    "page_start": page_start or 1,
                    "page_end": page_end or page_start or 1,
                    "section_title": current_section,
                    "element_type": "prose",
                    "content": chunk_text,
                    "metadata": {
                        "token_count": self._approx_token_count(chunk_text),
                        "sentence_count": len(chunk_sentences)
                    }
                })

            prose_buffer = []
            page_start = None
            page_end = None

        for el in elements:
            el_type = el.get("element_type")
            page = el.get("page_number", 1)
            content = el.get("content", "").strip()

            if not content:
                continue

            # If element is a Heading, update section context and flush prior text
            if el_type == "heading":
                flush_prose_buffer()
                current_section = content
                page_start = page
                page_end = page
                continue

            # Tables and figures are self-contained layout elements: keep them distinct
            if el_type in ("table", "figure"):
                flush_prose_buffer()
                chunks.append({
                    "document_id": document_id,
                    "workspace_id": workspace_id,
                    "page_start": page,
                    "page_end": page,
                    "section_title": f"{current_section} ({el_type.capitalize()})",
                    "element_type": el_type,
                    "content": content,
                    "metadata": el.get("metadata", {})
                })
                continue

            # Prose paragraph or OCR text
            if page_start is None:
                page_start = page
            page_end = page
            prose_buffer.append(content)

        flush_prose_buffer()
        logger.info(f"Chunking complete: produced {len(chunks)} chunks for document {document_id}")
        return chunks

layout_chunker = LayoutAwareChunker()
