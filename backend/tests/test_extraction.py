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


def test_universal_profile_extracts_topics_terms_and_citations(extraction_db):
    extraction_db.add(DocumentChunk(
        id="c_algorithm_1",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=2,
        page_end=2,
        section_title="Algorithm",
        content="An algorithm is a finite sequence of clear instructions that solves a problem.",
    ))
    extraction_db.add(DocumentChunk(
        id="c_dates_1",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=3,
        page_end=3,
        section_title="Examples",
        content="The course started in Q1 2026 and uses 25 percent fewer steps.",
    ))
    extraction_db.add(DocumentChunk(
        id="c_table_1",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=4,
        page_end=4,
        element_type="table",
        section_title="Conclusion (Table)",
        content="| Term | Definition |",
    ))
    extraction_db.add(DocumentChunk(
        id="c_table_header_1",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=4,
        page_end=4,
        section_title="Term\nDefinition\nSignificance",
        content="Table header content",
    ))
    extraction_db.commit()

    result = StructuredExtractor().extract(
        extraction_db, "doc_p1", "ws_1", "universal_document"
    )

    assert result["schema_name"] == "universal_document"
    assert result["extracted_data"]["document_type"] == "Educational or study material"
    assert "Algorithm" in result["extracted_data"]["main_topics"]
    assert "Conclusion (Table)" not in result["extracted_data"]["main_topics"]
    assert "Term Definition Significance" not in result["extracted_data"]["main_topics"]
    assert any(term["term"] == "Algorithm" for term in result["extracted_data"]["key_terms"])
    assert "Q1 2026" in result["extracted_data"]["dates"]
    assert result["field_citations"]["key_terms"][0]["page_number"] == 2


def test_custom_fields_can_target_a_document_heading(extraction_db):
    extraction_db.add(DocumentChunk(
        id="c_algorithm_2",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=2,
        page_end=2,
        section_title="Algorithm",
        content="A finite sequence of precise instructions for solving a problem.",
    ))
    extraction_db.add(DocumentChunk(
        id="c_algorithm_related",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=86,
        page_end=86,
        section_title="Algorithm-",
        content="Algorithm-centric improvements optimize code performance.",
    ))
    extraction_db.commit()
    custom_schema = {
        "title": "Custom fields",
        "properties": {
            "algorithm_definition": {
                "title": "Algorithm",
                "type": "string",
                "description": "Definition of the algorithm concept",
            },
        },
        "required": ["algorithm_definition"],
    }

    result = StructuredExtractor().extract(
        extraction_db, "doc_p1", "ws_1", "custom_document", custom_schema
    )

    assert "precise instructions" in result["extracted_data"]["algorithm_definition"]
    assert result["validation"]["is_valid"] is True
    assert result["field_citations"]["algorithm_definition"]["page_number"] == 2


def test_custom_field_description_can_match_a_relevant_passage(extraction_db):
    extraction_db.add(DocumentChunk(
        id="c_algorithm_description",
        document_id="doc_p1",
        workspace_id="ws_1",
        page_start=5,
        page_end=5,
        section_title="How Algorithms Work",
        content="An algorithm is a finite sequence of precise instructions used to solve a problem.",
    ))
    extraction_db.commit()
    custom_schema = {
        "title": "Custom fields",
        "properties": {
            "approach": {
                "title": "Algorithm definition",
                "type": "string",
                "description": "Finite sequence of precise instructions used to solve a problem",
            },
        },
    }

    result = StructuredExtractor().extract(
        extraction_db, "doc_p1", "ws_1", "custom_document", custom_schema
    )

    assert "finite sequence" in result["extracted_data"]["approach"].lower()
    assert result["field_citations"]["approach"]["page_number"] == 5


def test_unknown_schema_is_not_silently_replaced_with_proposal_schema(extraction_db):
    with pytest.raises(ValueError, match="Unknown extraction template"):
        StructuredExtractor().extract(
            extraction_db, "doc_p1", "ws_1", "not_a_template"
        )
