import pytest
from app.chunking.layout_chunker import LayoutAwareChunker

def test_chunker_preserves_headings_and_tables():
    chunker = LayoutAwareChunker(target_chunk_size=100, overlap_size=20)
    elements = [
        {
            "element_type": "heading",
            "page_number": 1,
            "content": "1. Executive Summary"
        },
        {
            "element_type": "paragraph",
            "page_number": 1,
            "content": "DocuMind is an enterprise-grade document intelligence platform designed to extract facts and verify citations."
        },
        {
            "element_type": "table",
            "page_number": 2,
            "content": "| Metric | Target |\n| --- | --- |\n| Recall | 95% |",
            "metadata": {"headers": ["Metric", "Target"]}
        },
        {
            "element_type": "paragraph",
            "page_number": 2,
            "content": "Future iterations will expand multimodal capability across more file types."
        }
    ]

    chunks = chunker.chunk_elements(elements, "doc_test_1", "ws_test_1")
    assert len(chunks) >= 3

    # Heading context propagated
    prose_chunk = next(c for c in chunks if c["element_type"] == "prose")
    assert prose_chunk["section_title"] == "1. Executive Summary"
    assert "DocuMind" in prose_chunk["content"]

    # Table kept as standalone unit
    table_chunk = next(c for c in chunks if c["element_type"] == "table")
    assert table_chunk["page_start"] == 2
    assert "Recall" in table_chunk["content"]
