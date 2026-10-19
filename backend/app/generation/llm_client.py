import json
import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.observability.logger import logger
from app.generation.grounded_prompts import GROUNDED_SYSTEM_INSTRUCTION, build_evidence_context

class LLMClient:
    """
    LLM Client for Grounded Question Answering and Structured Information Processing.
    Uses Gemini API with structured JSON output, with a reliable offline synthesis fallback.
    """

    def __init__(self):
        self._model = None

    def _get_model(self):
        if not settings.GEMINI_API_KEY:
            return None
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=GROUNDED_SYSTEM_INSTRUCTION,
                    generation_config={"response_mime_type": "application/json"}
                )
            except Exception as e:
                logger.error(f"Failed to configure Gemini model: {e}")
                self._model = None
        return self._model

    def _fallback_generate(self, question: str, evidence_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extractive synthesis fallback for offline/test environments.
        Matches question terms in evidence, compiles findings with citations or abstains.
        """
        if not evidence_chunks:
            return {
                "answer": "The available documents do not contain information related to this question.",
                "citations": [],
                "insufficient_evidence": True
            }

        # Ignore common English stop words for relevance determination
        STOP_WORDS = {"what", "were", "where", "when", "which", "whose", "whom", "this", "that", "these", "those", "from", "with", "about", "into", "over", "after", "before", "between", "under", "personal", "sale"}
        q_terms = set(re.findall(r'\b\w{3,}\b', question.lower())) - STOP_WORDS
        matched_chunks = []
        citations = []

        for c in evidence_chunks:
            c_text = c.get("content", "")
            matches = [t for t in q_terms if t in c_text.lower()]
            if len(matches) >= 2 or (len(q_terms) == 1 and len(matches) == 1):
                matched_chunks.append((c, len(matches)))
                sentences = re.split(r'(?<=[.!?])\s+', c_text)
                quote = sentences[0] if sentences else c_text[:120]
                citations.append({
                    "chunk_id": c.get("chunk_id", ""),
                    "document_id": c.get("document_id", ""),
                    "page_number": c.get("page_start", 1),
                    "quote": quote.strip()
                })

        if not matched_chunks:
            return {
                "answer": f"DocuMind could not locate sufficient evidence in the uploaded documents to answer '{question}'.",
                "citations": [],
                "insufficient_evidence": True
            }

        matched_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = matched_chunks[:3]

        answer_bullets = []
        for i, (chunk, _) in enumerate(top_chunks, 1):
            p = chunk.get("page_start", 1)
            sec = chunk.get("section_title", "General")
            snip = chunk.get("content", "").strip()[:200]
            answer_bullets.append(f"{i}. Based on {sec} (Page {p}): {snip}...")

        answer = "Based on the retrieved document evidence:\n\n" + "\n\n".join(answer_bullets)

        return {
            "answer": answer,
            "citations": citations[:3],
            "insufficient_evidence": False
        }

    def generate_grounded_answer(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not evidence_chunks:
            return {
                "answer": "No relevant document evidence was retrieved for this inquiry.",
                "citations": [],
                "insufficient_evidence": True
            }

        model = self._get_model()
        if not model:
            return self._fallback_generate(question, evidence_chunks)

        context_str = build_evidence_context(evidence_chunks)
        user_prompt = f"USER QUESTION:\n{question}\n\nRETRIEVED DOCUMENT EVIDENCE:\n{context_str}"

        try:
            response = model.generate_content(user_prompt)
            data = json.loads(response.text)
            return data
        except Exception as e:
            logger.error(f"Error during Gemini grounded answer generation: {e}")
            return self._fallback_generate(question, evidence_chunks)

llm_client = LLMClient()
