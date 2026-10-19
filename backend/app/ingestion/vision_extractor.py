import fitz
import io
from typing import List, Dict, Any, Optional
from PIL import Image
from app.config import settings
from app.observability.logger import logger

class VisionExtractor:
    """
    Interprets charts, diagrams, and figures using Gemini multimodal vision API.
    """

    def __init__(self):
        self._genai_client = None

    def _get_model(self):
        if not settings.GEMINI_API_KEY:
            return None
        if self._genai_client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._genai_client = genai.GenerativeModel(settings.GEMINI_MODEL)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini vision client: {e}")
                return None
        return self._genai_client

    def extract_visuals(self, file_path: str, document_id: str, target_pages: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        elements: List[Dict[str, Any]] = []
        model = self._get_model()
        if not model:
            logger.info("Vision analysis skipped: No GEMINI_API_KEY provided.")
            return elements

        try:
            doc = fitz.open(file_path)
            pages_to_check = target_pages if target_pages else range(1, min(len(doc) + 1, 15))

            for page_num in pages_to_check:
                page_idx = page_num - 1
                if page_idx >= len(doc):
                    continue
                page = doc[page_idx]
                image_list = page.get_images(full=True)

                if image_list:
                    # Page contains images/figures, render high-res
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))

                    prompt = (
                        "Analyze this document page. Focus strictly on any charts, graphs, flowcharts, "
                        "architecture diagrams, or tables present. Describe their axes, data values, "
                        "trends, legends, and key takeaways concisely for factual search indexing."
                    )
                    
                    response = model.generate_content([prompt, img])
                    description = response.text.strip() if response and response.text else ""

                    if description:
                        elements.append({
                            "document_id": document_id,
                            "page_number": page_num,
                            "element_type": "figure",
                            "content": f"[Visual Chart/Diagram Analysis - Page {page_num}]\n{description}",
                            "source_method": "gemini_multimodal_vision",
                            "bounding_box": None,
                            "metadata": {
                                "image_count": len(image_list),
                                "model": settings.GEMINI_MODEL
                            }
                        })
                        logger.info(f"Vision analysis completed for page {page_num} of {document_id}")

            doc.close()
        except Exception as e:
            logger.error(f"Error during vision extraction: {e}")

        return elements

vision_extractor = VisionExtractor()
