import fitz
from typing import List, Dict, Any, Optional
from PIL import Image
import io
from app.observability.logger import logger

class OCRExtractor:
    def __init__(self):
        self._tesseract_available = None

    def is_available(self) -> bool:
        if self._tesseract_available is None:
            try:
                import pytesseract
                # Test call with dummy image
                dummy = Image.new("RGB", (30, 30), color="white")
                pytesseract.image_to_string(dummy)
                self._tesseract_available = True
            except Exception as e:
                logger.warning(f"Tesseract OCR not available on host system: {e}")
                self._tesseract_available = False
        return self._tesseract_available

    def process_scanned_pages(
        self,
        file_path: str,
        document_id: str,
        page_numbers: List[int]
    ) -> List[Dict[str, Any]]:
        elements: List[Dict[str, Any]] = []
        if not page_numbers:
            return elements

        if not self.is_available():
            logger.info("Skipping OCR processing because Tesseract binary is not installed.")
            return elements

        import pytesseract

        doc = fitz.open(file_path)
        for page_num in page_numbers:
            try:
                page_idx = page_num - 1
                if page_idx >= len(doc):
                    continue
                page = doc[page_idx]
                
                # Render page to high-res image (300 DPI)
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                # Run OCR with detailed data to get confidence
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(img).strip()

                confs = [int(c) for c in ocr_data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
                avg_conf = sum(confs) / len(confs) if confs else 0.0

                if text:
                    elements.append({
                        "document_id": document_id,
                        "page_number": page_num,
                        "element_type": "ocr_text",
                        "content": text,
                        "source_method": "tesseract_ocr",
                        "bounding_box": None,
                        "metadata": {
                            "ocr_confidence": round(avg_conf, 2),
                            "low_confidence": avg_conf < 60.0
                        }
                    })
                    logger.info(f"OCR extracted text from page {page_num} with confidence {avg_conf:.1f}%")
            except Exception as e:
                logger.error(f"OCR failed for page {page_num}: {e}")

        doc.close()
        return elements

ocr_extractor = OCRExtractor()
