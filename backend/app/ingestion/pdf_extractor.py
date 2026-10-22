import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
from pathlib import Path
from app.observability.logger import logger

class PDFExtractor:
    """
    Extracts text blocks, headings, layout coordinates and detects scanned/empty pages using PyMuPDF.
    """

    def extract_document(self, file_path: str, document_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        elements: List[Dict[str, Any]] = []
        doc = fitz.open(file_path)
        page_count = len(doc)
        scanned_pages: List[int] = []
        total_text_length = 0

        for page_num in range(page_count):
            page = doc[page_num]
            one_based_page = page_num + 1
            
            # Extract text blocks with coordinates: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type 0 = text, 1 = image
            blocks = page.get_text("blocks")
            page_text_length = 0

            for b in blocks:
                if b[6] == 0:  # text block
                    text = b[4].strip()
                    if not text:
                        continue

                    # Ignore placeholder text from image-to-PDF converters.
                    normalized = " ".join(text.lower().split()).strip(" .:-")
                    if normalized in {"image to pdf", "image to pdf converter"}:
                        continue
                    
                    page_text_length += len(text)
                    bbox = {"x0": round(b[0], 2), "y0": round(b[1], 2), "x1": round(b[2], 2), "y1": round(b[3], 2)}
                    
                    # Heuristic for headings vs paragraph:
                    # Short text (< 80 chars), doesn't end with period, capitalized or all-caps
                    is_heading = len(text) < 80 and not text.endswith(".") and (text.isupper() or text.istitle())
                    element_type = "heading" if is_heading else "paragraph"

                    elements.append({
                        "document_id": document_id,
                        "page_number": one_based_page,
                        "element_type": element_type,
                        "content": text,
                        "source_method": "pdf_text_extractor",
                        "bounding_box": bbox,
                        "metadata": {
                            "block_number": b[5],
                            "is_heading": is_heading,
                        }
                    })

            total_text_length += page_text_length
            
            # Flag suspiciously empty or low-text pages (< 50 characters) as potential scanned pages
            if page_text_length < 50:
                scanned_pages.append(one_based_page)

        doc.close()

        summary = {
            "page_count": page_count,
            "total_elements": len(elements),
            "total_text_length": total_text_length,
            "scanned_pages": scanned_pages,
            "has_scanned_pages": len(scanned_pages) > 0,
        }

        logger.info(
            f"PDF Extraction completed for {document_id}: {page_count} pages, {len(elements)} elements, {len(scanned_pages)} suspected scanned pages."
        )

        return elements, summary

pdf_extractor = PDFExtractor()
