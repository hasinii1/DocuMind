import json
import csv
import io
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import DocumentChunk, ExtractionRun
from app.config import settings
from app.observability.logger import logger

BUILTIN_SCHEMAS = {
    "project_proposal": {
        "title": "Project Proposal Schema",
        "description": "Extracts standard deliverables, timeline, budget, and project metadata.",
        "properties": {
            "project_name": {"type": "string", "description": "Official title of the project"},
            "deadline": {"type": "string", "description": "Target completion date (YYYY-MM-DD)"},
            "budget": {"type": "number", "description": "Total proposed budget or monetary value"},
            "lead_organization": {"type": "string", "description": "Name of proposing company or lead"},
            "requirements": {"type": "array", "description": "Key technical or operational requirements"}
        },
        "required": ["project_name", "budget"]
    },
    "contract_agreement": {
        "title": "Commercial Agreement Schema",
        "description": "Extracts parties, effective date, governing law, and payment terms.",
        "properties": {
            "party_a": {"type": "string", "description": "First contracting entity"},
            "party_b": {"type": "string", "description": "Second contracting entity"},
            "effective_date": {"type": "string", "description": "Agreement start date"},
            "term_length": {"type": "string", "description": "Duration or expiration clause"},
            "governing_law": {"type": "string", "description": "Jurisdiction / applicable law"},
            "payment_terms": {"type": "string", "description": "Net payment schedule or terms"}
        },
        "required": ["party_a", "party_b", "governing_law"]
    },
    "financial_statement": {
        "title": "Financial Report Highlights",
        "description": "Extracts revenue, operating expenses, net profit, and reporting period.",
        "properties": {
            "reporting_period": {"type": "string", "description": "Fiscal year or quarter (e.g. Q1 2026)"},
            "total_revenue": {"type": "number", "description": "Total recorded revenue"},
            "operating_expenses": {"type": "number", "description": "Total operating expenses"},
            "net_income": {"type": "number", "description": "Net profit or loss"}
        },
        "required": ["reporting_period", "total_revenue"]
    }
}

class StructuredExtractor:
    """
    Extracts structured fields matching a user-defined or built-in JSON schema,
    attaching citations to each field and enabling CSV/JSON export.
    """

    def _extract_heuristically(
        self,
        schema: Dict[str, Any],
        chunks: List[DocumentChunk]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        full_text = " ".join([c.content for c in chunks])
        extracted: Dict[str, Any] = {}
        field_citations: Dict[str, Any] = {}

        properties = schema.get("properties", {})
        for field, spec in properties.items():
            f_type = spec.get("type", "string")
            clean_field_name = field.replace("_", " ")

            # Search text for field pattern
            pattern = rf"(?i)\b{re.escape(clean_field_name)}\b[:\s\-]+([^\n\r.]+)"
            match = re.search(pattern, full_text)

            if match:
                raw_val = match.group(1).strip()
                # Find matching chunk for citation
                matching_chunk = next((c for c in chunks if raw_val in c.content), chunks[0] if chunks else None)
                
                if f_type == "number":
                    num_match = re.search(r'[\d,]+(?:\.\d+)?', raw_val)
                    val = float(num_match.group(0).replace(",", "")) if num_match else None
                elif f_type == "array":
                    val = [item.strip() for item in raw_val.split(",") if item.strip()]
                else:
                    val = raw_val

                extracted[field] = val
                if matching_chunk:
                    field_citations[field] = {
                        "chunk_id": matching_chunk.id,
                        "page_number": matching_chunk.page_start,
                        "quote": match.group(0)
                    }
            else:
                extracted[field] = None  # Explicit None indicates absent/unfound field

        return extracted, field_citations

    def extract(
        self,
        db: Session,
        document_id: str,
        workspace_id: str,
        schema_name: str,
        custom_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        schema = custom_schema if custom_schema else BUILTIN_SCHEMAS.get(schema_name, BUILTIN_SCHEMAS["project_proposal"])

        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.workspace_id == workspace_id
        ).order_by(DocumentChunk.page_start).all()

        if not chunks:
            raise ValueError("No processed document chunks found for extraction.")

        extracted_data, field_citations = self._extract_heuristically(schema, chunks)

        # Validate required fields
        required_fields = schema.get("required", [])
        missing_required = [f for f in required_fields if extracted_data.get(f) is None]

        return {
            "schema_name": schema_name,
            "target_schema": schema,
            "extracted_data": extracted_data,
            "field_citations": field_citations,
            "validation": {
                "is_valid": len(missing_required) == 0,
                "missing_required": missing_required
            }
        }

    def export_to_csv(self, extracted_data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Field", "Value", "Status"])
        for k, v in extracted_data.items():
            status = "Extracted" if v is not None else "Absent / Missing"
            writer.writerow([k, json.dumps(v) if isinstance(v, (list, dict)) else str(v or ""), status])
        return output.getvalue()

structured_extractor = StructuredExtractor()
