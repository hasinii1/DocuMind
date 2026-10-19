import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Document, DocumentChunk
from app.citations.validator import CitationValidator

@pytest.fixture
def mock_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    doc = Document(
        id="doc_1",
        workspace_id="ws_1",
        title="Annual Cost Report",
        original_filename="cost_report.pdf",
        mime_type="application/pdf",
        file_size_bytes=1000,
        checksum="abc12345",
        storage_path="/tmp/mock.pdf"
    )
    db.add(doc)

    chunk = DocumentChunk(
        id="chunk_valid_1",
        document_id="doc_1",
        workspace_id="ws_1",
        page_start=12,
        page_end=12,
        section_title="Operating Expenses",
        content="Operating costs increased primarily due to expanded cloud infrastructure and specialized engineering hires."
    )
    db.add(chunk)
    db.commit()

    yield db
    db.close()

def test_citation_validator_accepts_valid_quote(mock_db):
    validator = CitationValidator()
    retrieved_chunks = [{
        "chunk_id": "chunk_valid_1",
        "document_id": "doc_1",
        "page_start": 12,
        "content": "Operating costs increased primarily due to expanded cloud infrastructure and specialized engineering hires."
    }]

    raw_citations = [{
        "chunk_id": "chunk_valid_1",
        "document_id": "fake_doc_id_invented_by_llm",
        "page_number": 999, # LLM hallucinated page
        "quote": "cloud infrastructure and specialized engineering"
    }]

    validated = validator.validate_citations(mock_db, raw_citations, retrieved_chunks, "ws_1")
    assert len(validated) == 1
    c = validated[0]
    # Trusted DB values should override hallucinated ones
    assert c["chunk_id"] == "chunk_valid_1"
    assert c["document_id"] == "doc_1"
    assert c["page_number"] == 12
    assert c["is_verified"] is True
    assert c["confidence_score"] >= 0.8

def test_citation_validator_rejects_unretrieved_or_unauthorized_chunk(mock_db):
    validator = CitationValidator()
    # Chunk wasn't in retrieved set
    retrieved_chunks = []
    raw_citations = [{
        "chunk_id": "chunk_valid_1",
        "quote": "Operating costs"
    }]

    validated = validator.validate_citations(mock_db, raw_citations, retrieved_chunks, "ws_1")
    assert len(validated) == 0
