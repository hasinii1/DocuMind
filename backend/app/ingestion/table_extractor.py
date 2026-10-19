import fitz
from typing import List, Dict, Any
from app.observability.logger import logger

class TableExtractor:
    """
    Extracts tabular data preserving row, column, and header structure.
    """

    def extract_tables(self, file_path: str, document_id: str) -> List[Dict[str, Any]]:
        elements: List[Dict[str, Any]] = []
        try:
            doc = fitz.open(file_path)
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                one_based_page = page_idx + 1

                # Use PyMuPDF's find_tables feature
                tables = page.find_tables()
                for table_idx, tab in enumerate(tables):
                    extracted_tab = tab.extract()
                    if not extracted_tab or len(extracted_tab) < 2:
                        continue

                    # Header row
                    headers = [str(c or "").strip() for c in extracted_tab[0]]
                    rows = []
                    markdown_lines = []
                    markdown_lines.append("| " + " | ".join(headers) + " |")
                    markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

                    for r in extracted_tab[1:]:
                        clean_row = [str(c or "").strip() for c in r]
                        rows.append(clean_row)
                        markdown_lines.append("| " + " | ".join(clean_row) + " |")

                    markdown_content = "\n".join(markdown_lines)
                    bbox = tab.bbox # (x0, y0, x1, y1)

                    elements.append({
                        "document_id": document_id,
                        "page_number": one_based_page,
                        "element_type": "table",
                        "content": markdown_content,
                        "source_method": "pymupdf_table_extractor",
                        "bounding_box": {
                            "x0": round(bbox[0], 2),
                            "y0": round(bbox[1], 2),
                            "x1": round(bbox[2], 2),
                            "y1": round(bbox[3], 2)
                        },
                        "metadata": {
                            "table_index": table_idx,
                            "headers": headers,
                            "rows": rows,
                            "row_count": len(rows),
                            "col_count": len(headers)
                        }
                    })

            doc.close()
            logger.info(f"Table extraction found {len(elements)} tables for document {document_id}")
        except Exception as e:
            logger.error(f"Error during table extraction: {e}")

        return elements

table_extractor = TableExtractor()
