import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, DocumentChunk
from app.comparison.differ import DocumentDiffer

@pytest.fixture
def comparison_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # V1 chunks
    db.add(DocumentChunk(
        id="v1_c1",
        document_id="doc_v1",
        workspace_id="ws_1",
        page_start=1,
        page_end=1,
        section_title="Budget",
        content="The agreed total project budget is $500,000 payable across three milestones."
    ))

    # V2 chunks (budget changed to $650,000)
    db.add(DocumentChunk(
        id="v2_c1",
        document_id="doc_v2",
        workspace_id="ws_1",
        page_start=1,
        page_end=1,
        section_title="Budget",
        content="The agreed total project budget is $650,000 payable across three milestones."
    ))

    # V2 chunk added (new SLA section)
    db.add(DocumentChunk(
        id="v2_c2",
        document_id="doc_v2",
        workspace_id="ws_1",
        page_start=2,
        page_end=2,
        section_title="Service Level Agreement",
        content="The contractor shall maintain 99.9% uptime for cloud services."
    ))

    db.commit()
    yield db
    db.close()

def test_document_differ_detects_numerical_and_structural_changes(comparison_db):
    differ = DocumentDiffer()
    result = differ.compare_documents(comparison_db, "doc_v1", "doc_v2", "ws_1")

    assert result["total_changes"] >= 1
    assert result["statistics"]["critical"] >= 1
    
    # Check that altered numerical value ($500,000 vs $650,000) was flagged as critical
    crit_change = next(c for c in result["changes"] if c["significance"] == "critical")
    assert "$500,000" in crit_change["old_text"]
    assert "$650,000" in crit_change["new_text"]
