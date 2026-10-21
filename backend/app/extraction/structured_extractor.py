import csv
import io
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk

UNIVERSAL_SCHEMA: Dict[str, Any] = {
    "title": "Universal Document Profile",
    "description": "A general-purpose, evidence-linked overview of the document.",
    "properties": {
        "document_type": {
            "type": "string",
            "title": "Document type",
            "description": "Likely document category based on its content.",
        },
        "overview": {
            "type": "string",
            "title": "Overview",
            "description": "An extractive preview from the document introduction or first section.",
        },
        "main_topics": {
            "type": "array",
            "title": "Main topics",
            "description": "Distinct section headings found in the document.",
        },
        "key_terms": {
            "type": "array",
            "title": "Key terms and definitions",
            "description": "Terms inferred from section headings with their source text.",
        },
        "key_facts": {
            "type": "array",
            "title": "Key facts",
            "description": "Representative text passages organized by section.",
        },
        "dates": {
            "type": "array",
            "title": "Dates and periods",
            "description": "Dates and quarter/year references written in the document.",
        },
        "key_figures": {
            "type": "array",
            "title": "Key figures",
            "description": "Numbers with nearby currency, percentage, or scale context.",
        },
    },
    "required": ["overview"],
}

BUILTIN_SCHEMAS = {
    "universal_document": UNIVERSAL_SCHEMA,
    "project_proposal": {
        "title": "Project Proposal Schema",
        "description": "Extracts standard deliverables, timeline, budget, and project metadata.",
        "properties": {
            "project_name": {"type": "string", "description": "Official title of the project"},
            "deadline": {"type": "string", "description": "Target completion date (YYYY-MM-DD)"},
            "budget": {"type": "number", "description": "Total proposed budget or monetary value"},
            "lead_organization": {"type": "string", "description": "Name of proposing company or lead"},
            "requirements": {"type": "array", "description": "Key technical or operational requirements"},
        },
        "required": ["project_name", "budget"],
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
            "payment_terms": {"type": "string", "description": "Net payment schedule or terms"},
        },
        "required": ["party_a", "party_b", "governing_law"],
    },
    "financial_statement": {
        "title": "Financial Report Highlights",
        "description": "Extracts revenue, operating expenses, net profit, and reporting period.",
        "properties": {
            "reporting_period": {"type": "string", "description": "Fiscal year or quarter (e.g. Q1 2026)"},
            "total_revenue": {"type": "number", "description": "Total recorded revenue"},
            "operating_expenses": {"type": "number", "description": "Total operating expenses"},
            "net_income": {"type": "number", "description": "Net profit or loss"},
        },
        "required": ["reporting_period", "total_revenue"],
    },
}

UNIVERSAL_FIELDS = set(UNIVERSAL_SCHEMA["properties"])
GENERIC_HEADINGS = {
    "abstract",
    "appendix",
    "contents",
    "conclusion",
    "conclusion table",
    "detailed analysis",
    "executive summary",
    "introduction",
    "definition",
    "key takeaways",
    "overview",
    "references",
    "significance",
    "table",
    "term",
    "term definition significance",
}
STOP_WORDS = {
    "about", "and", "are", "for", "from", "how", "into", "the", "their",
    "this", "what", "when", "where", "which", "with",
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("|", " ")).strip()


def _citation(chunk: DocumentChunk, quote: str) -> Dict[str, Any]:
    return {
        "chunk_id": chunk.id,
        "page_number": chunk.page_start,
        "quote": quote,
    }


class StructuredExtractor:
    """Extracts general document profiles and user-selected fields with page citations."""

    def _extract_universal(
        self, chunks: List[DocumentChunk]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        text_chunks = [chunk for chunk in chunks if chunk.element_type != "table"]
        all_text = "\n".join(chunk.content for chunk in chunks)
        normalized_text = all_text.lower()

        if any(term in normalized_text for term in ("lecture", "lesson", "course", "algorithm", "students", "learning objectives")):
            document_type = "Educational or study material"
        elif any(term in normalized_text for term in ("governing law", "payment terms", "agreement between", "hereby agree")):
            document_type = "Contract or agreement"
        elif any(term in normalized_text for term in ("balance sheet", "net income", "operating expenses", "total revenue")):
            document_type = "Financial report"
        elif any(term in normalized_text for term in ("proposal", "project objective", "deliverables", "project timeline")):
            document_type = "Project proposal"
        elif any(term in normalized_text for term in ("abstract", "methodology", "results", "references")):
            document_type = "Research or technical document"
        else:
            document_type = "General document"

        overview_chunk = next(
            (
                chunk for chunk in text_chunks
                if (chunk.section_title or "").strip().lower()
                in {"introduction", "abstract", "summary", "executive summary", "overview"}
                and len(chunk.content.strip()) > 40
            ),
            next((chunk for chunk in text_chunks if len(chunk.content.strip()) > 40), None),
        )
        overview = ""
        citations: Dict[str, Any] = {}
        if overview_chunk:
            overview = _clean_text(overview_chunk.content)
            if len(overview) > 750:
                overview = overview[:750].rsplit(" ", 1)[0]
            citations["overview"] = _citation(overview_chunk, overview)

        topic_chunks: Dict[str, DocumentChunk] = {}
        for chunk in chunks:
            if chunk.element_type == "table":
                continue
            title = _clean_text(chunk.section_title or "").strip(" -:#()")
            key = title.casefold()
            if (
                not title
                or len(title) > 90
                or key in GENERIC_HEADINGS
                or title.startswith("#")
                or key.startswith("output:")
                or key.startswith("week ")
            ):
                continue
            topic_chunks.setdefault(title, chunk)

        topics = list(topic_chunks)[:12]
        if topics:
            citations["main_topics"] = [
                _citation(topic_chunks[topic], topic) for topic in topics
            ]

        terms: List[Dict[str, Any]] = []
        term_citations: List[Dict[str, Any]] = []
        for title, chunk in topic_chunks.items():
            definition = _clean_text(chunk.content)
            if len(definition) < 35:
                continue
            terms.append({
                "term": title,
                "definition": definition[:500],
                "page_number": chunk.page_start,
            })
            term_citations.append(_citation(chunk, definition[:500]))
            if len(terms) >= 12:
                break
        if term_citations:
            citations["key_terms"] = term_citations[:12]

        key_facts: List[Dict[str, Any]] = []
        fact_citations: List[Dict[str, Any]] = []
        seen_facts = set()
        for chunk in text_chunks:
            section = _clean_text(chunk.section_title or "Document")
            fact = _clean_text(chunk.content)
            if len(fact) < 70 or fact.casefold() in seen_facts:
                continue
            seen_facts.add(fact.casefold())
            fact = fact[:360].rsplit(" ", 1)[0]
            key_facts.append({
                "section": section,
                "fact": fact,
                "page_number": chunk.page_start,
            })
            fact_citations.append(_citation(chunk, fact))
            if len(key_facts) >= 12:
                break
        if fact_citations:
            citations["key_facts"] = fact_citations

        dates = list(dict.fromkeys(re.findall(
            r"\b(?:\d{4}-\d{1,2}-\d{1,2}|"
            r"(?:Q[1-4]\s+)?(?:19|20)\d{2}|"
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
            r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
            r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2})\b",
            all_text,
            flags=re.IGNORECASE,
        )))[:12]
        date_citations = self._citations_for_values(dates, chunks)
        if date_citations:
            citations["dates"] = date_citations

        figures: List[Dict[str, Any]] = []
        figure_citations: List[Dict[str, Any]] = []
        figure_pattern = re.compile(
            r"(?<!\w)(?:[$€£]\s*\d[\d,]*(?:\.\d+)?|"
            r"\d[\d,]*(?:\.\d+)?\s*(?:%|percent|million|billion|"
            r"thousand|USD|EUR|GBP|dollars?))\b",
            re.IGNORECASE,
        )
        seen_figures = set()
        for chunk in chunks:
            for match in figure_pattern.finditer(chunk.content):
                value = match.group(0).strip()
                if value.casefold() in seen_figures:
                    continue
                seen_figures.add(value.casefold())
                start = max(0, match.start() - 100)
                end = min(len(chunk.content), match.end() + 100)
                context = _clean_text(chunk.content[start:end])
                figures.append({
                    "value": value,
                    "context": context,
                    "page_number": chunk.page_start,
                })
                figure_citations.append(_citation(chunk, context))
                if len(figures) >= 12:
                    break
            if len(figures) >= 30:
                break
        if figure_citations:
            citations["key_figures"] = figure_citations[:12]

        data = {
            "document_type": document_type,
            "overview": overview or None,
            "main_topics": topics,
            "key_terms": terms,
            "key_facts": key_facts,
            "dates": dates,
            "key_figures": figures,
        }
        return data, citations

    @staticmethod
    def _citations_for_values(values: List[str], chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        citations = []
        for value in values[:12]:
            chunk = next(
                (item for item in chunks if value.casefold() in item.content.casefold()),
                None,
            )
            if chunk:
                citations.append(_citation(chunk, value))
        return citations

    @staticmethod
    def _parse_value(raw_value: str, field_type: str) -> Any:
        if field_type == "number":
            number_match = re.search(r"-?[\d,]+(?:\.\d+)?", raw_value)
            return float(number_match.group(0).replace(",", "")) if number_match else None
        if field_type == "array":
            return [
                item.strip(" \t-•")
                for item in re.split(r"[,;\n]+", raw_value)
                if item.strip(" \t-•")
            ]
        if field_type == "boolean":
            normalized = raw_value.strip().casefold()
            if normalized in {"yes", "true", "present"}:
                return True
            if normalized in {"no", "false", "absent"}:
                return False
            return None
        return raw_value.strip()

    def _extract_custom_fields(
        self,
        schema: Dict[str, Any],
        chunks: List[DocumentChunk],
        extracted: Dict[str, Any],
        citations: Dict[str, Any],
        excluded_fields: Optional[set] = None,
    ) -> None:
        excluded_fields = excluded_fields or set()
        for field, spec in schema.get("properties", {}).items():
            if field in excluded_fields:
                continue

            label = str(spec.get("title") or field.replace("_", " ").replace("-", " "))
            label_pattern = re.escape(label.strip())
            label_pattern = re.sub(r"\\\s+", r"[\\s_-]+", label_pattern)
            explicit_pattern = re.compile(
                rf"(?i)(?:^|[\n|.;])\s*{label_pattern}\s*[:=]\s*([^\n|.;]+)"
            )

            found = None
            for chunk in chunks:
                match = explicit_pattern.search(chunk.content)
                if match:
                    found = (chunk, match.group(1).strip())
                    break

            if not found:
                normalized_label = _clean_text(label).casefold()
                for chunk in chunks:
                    if _clean_text(chunk.section_title or "").casefold() == normalized_label:
                        found = (chunk, _clean_text(chunk.content))
                        break

            if not found:
                label_terms = [
                    term for term in re.findall(r"[a-z0-9]+", label.casefold())
                    if term not in STOP_WORDS and len(term) > 1
                ]
                description_terms = [
                    term for term in re.findall(
                        r"[a-z0-9]+", str(spec.get("description", "")).casefold()
                    )
                    if term not in STOP_WORDS and len(term) > 2
                ]
                min_matches = max(1, (len(label_terms) + 1) // 2)
                ranked = []
                for chunk in chunks:
                    title = (chunk.section_title or "").casefold()
                    content = chunk.content.casefold()
                    primary_title_match = bool(label_terms and label_terms[0] in title)
                    exact_primary_title = bool(
                        label_terms and title.strip() == label_terms[0]
                    )
                    label_title_matches = sum(term in title for term in label_terms)
                    label_content_matches = sum(term in content for term in label_terms)
                    description_matches = sum(
                        term in title or term in content for term in description_terms
                    )
                    if (
                        label_title_matches + label_content_matches >= min_matches
                        or description_matches
                    ):
                        score = (
                            exact_primary_title * 20
                            + primary_title_match * 8
                            + label_title_matches * 4
                            + label_content_matches * 2
                            + description_matches
                        )
                        ranked.append((score, chunk))
                if ranked:
                    _, chunk = max(ranked, key=lambda item: item[0])
                    found = (chunk, _clean_text(chunk.content)[:700])

            if found:
                chunk, raw_value = found
                value = self._parse_value(raw_value, spec.get("type", "string"))
                extracted[field] = value
                if value is not None:
                    citations[field] = _citation(chunk, raw_value[:500])
            else:
                extracted[field] = None

    def extract(
        self,
        db: Session,
        document_id: str,
        workspace_id: str,
        schema_name: str,
        custom_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        schema = custom_schema or BUILTIN_SCHEMAS.get(schema_name)
        if schema is None:
            raise ValueError(f"Unknown extraction template: {schema_name}")
        if not isinstance(schema.get("properties"), dict) or not schema["properties"]:
            raise ValueError("The extraction schema must define at least one field.")

        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.workspace_id == workspace_id,
        ).order_by(DocumentChunk.page_start).all()

        if not chunks:
            raise ValueError("No processed document chunks found for extraction.")

        is_universal_profile = (
            schema_name == "universal_document"
            or UNIVERSAL_FIELDS.issubset(schema["properties"])
        )
        if is_universal_profile:
            extracted_data, field_citations = self._extract_universal(chunks)
            self._extract_custom_fields(
                schema,
                chunks,
                extracted_data,
                field_citations,
                excluded_fields=UNIVERSAL_FIELDS,
            )
        else:
            extracted_data = {}
            field_citations = {}
            self._extract_custom_fields(schema, chunks, extracted_data, field_citations)

        required_fields = schema.get("required", [])
        missing_required = [
            field for field in required_fields if extracted_data.get(field) is None
        ]

        return {
            "schema_name": schema_name,
            "target_schema": schema,
            "extracted_data": extracted_data,
            "field_citations": field_citations,
            "validation": {
                "is_valid": len(missing_required) == 0,
                "missing_required": missing_required,
            },
        }

    def export_to_csv(self, extracted_data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Field", "Value", "Status"])
        for key, value in extracted_data.items():
            status = "Extracted" if value is not None else "Absent / Missing"
            serialized_value = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, (list, dict))
                else str(value or "")
            )
            writer.writerow([key, serialized_value, status])
        return output.getvalue()


structured_extractor = StructuredExtractor()
