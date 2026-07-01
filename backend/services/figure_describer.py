"""
Figure Describer Service
Uses PyMuPDF to extract figures and LLaVA to generate text descriptions
"""
import fitz  # PyMuPDF
import base64
import httpx
from typing import Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
LLAVA_MODEL = "llava"


class FigureDescriber:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._doc = None

    def _open(self):
        if self._doc is None:
            self._doc = fitz.open(self.pdf_path)

    def close(self):
        if self._doc:
            self._doc.close()
            self._doc = None

    def describe_figure_on_page(self, page_num: int, figure_index: int = 0, caption: str = "") -> Optional[str]:
        """
        Extract and describe a figure from a specific page.
        page_num is 1-indexed (matches Docling metadata).
        """
        self._open()
        try:
            page = self._doc[page_num - 1]
            image_list = page.get_images(full=True)

            if not image_list:
                logger.debug(f"[FigureDescriber] No images on page {page_num}")
                return None

            idx = min(figure_index, len(image_list) - 1)
            xref = image_list[idx][0]
            base_image = self._doc.extract_image(xref)
            b64 = base64.b64encode(base_image["image"]).decode("utf-8")

            return self._call_llava(b64, caption=caption)

        except Exception as e:
            logger.warning(f"[FigureDescriber] Extraction failed on page {page_num}: {e}")
            return None

    def _call_llava(self, b64_image: str, caption: str="") -> Optional[str]:
        caption_context = f'The figure\'s caption reads: "{caption}"\n\n' if caption else ""
    
        prompt = (
            "You are looking at a figure extracted from a research or academic document.\n"
            f"{caption_context}"
            "Describe ONLY what you can literally see in this specific image: "
            "the boxes, shapes, charts, or diagrams present; any text labels exactly as written; "
            "arrows and their direction; axes and their values if it's a graph; "
            "and the overall structure or layout.\n\n"
            "Do NOT invent steps, technologies, or labels that are not visibly present in the image. "
            "Do NOT assume a specific domain or technology unless it is explicitly visible as text in the image. "
            "If you cannot read a label clearly, say so rather than guessing. "
            "Base your description strictly on what is visually present, not on prior knowledge of typical "
            "diagrams in this field."
            )
        try:
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": LLAVA_MODEL,
                    "prompt": prompt,
                    "images": [b64_image],
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                },
                timeout=120.0
            )
            response.raise_for_status()
            description = response.json().get("response", "").strip()
            logger.info(f"[FigureDescriber] LLaVA generated description ({len(description)} chars)")
            return description or None

        except httpx.TimeoutException:
            logger.warning("[FigureDescriber] LLaVA timed out")
            return None
        except Exception as e:
            logger.warning(f"[FigureDescriber] LLaVA call failed: {e}")
            return None

    def is_llava_available(self) -> bool:
        try:
            response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            models = [m["name"] for m in response.json().get("models", [])]
            return any("llava" in m for m in models)
        except Exception:
            return False