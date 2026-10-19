import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, DocumentChunk
from app.extraction.structured_extractor import StructuredExtractor

@pytest.fixture
def extraction_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add(DocumentChunk(
        id="c_proposal_1",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=1,
        page_end=1,
        section_title="Overview",
        content="Project Name: DocuMind Enterprise AI. Budget: 750000. Lead Organization: DeepMind Engineering."
    ))
    db.commit()
    yield db
    db.close()

def test_structured_extraction_and_csv_export(extraction_db):
    extractor = StructuredExtractor()
    custom_schema = {
        "properties": {
            "project_name": {"type": "string"},
            "budget": {"type": "number"},
            "lead_organization": {"type": "string"},
            "missing_field": {"type": "string"}
        },
        "required": ["project_name", "budget"]
    }

    result = extractor.extract(
        extraction_db, "doc_p1", "ws_1", "custom_test", custom_schema
    )

    assert result["validation"]["is_valid"] is True
    data = result["extracted_data"]
    assert "DocuMind Enterprise AI" in data["project_name"]
    assert data["budget"] == 750000.0
    assert data["missing_field"] is None

    # Test CSV export
    csv_str = extractor.export_to_csv(data)
    assert "project_name" in csv_str
    assert "750000" in csv_str
    assert "Absent / Missing" in csv_str
