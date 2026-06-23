"""
Docling-based PDF Loader
Structure-aware document parsing with figure and table extraction
"""
from typing import List, Dict, Any, Optional

from annotated_types import doc
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument, DocItemLabel
import os


class StructuredDocument:
    def __init__(self, filename, title, elements, total_pages):
        self.filename = filename
        self.title = title
        self.elements = elements
        self.total_pages = total_pages

    def get_elements_by_type(self, element_type):
        return [e for e in self.elements if e.get("type") == element_type]

    def get_figures(self):
        return self.get_elements_by_type("figure")

    def get_tables(self):
        return self.get_elements_by_type("table")

    def __repr__(self):
        return f"StructuredDocument(filename={self.filename}, elements={len(self.elements)}, pages={self.total_pages})"


class DoclingLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.converter = DocumentConverter()

    def load(self) -> StructuredDocument:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")

        try:
            print(f"[DoclingLoader] Processing: {self.filename}")
            result = self.converter.convert(self.file_path)
            doc: DoclingDocument = result.document

            elements = self._extract_structured_elements(doc)
            total_pages = self._get_total_pages(doc)
            title = self._extract_title(doc)

            print(f"[DoclingLoader] Extracted {len(elements)} elements from {total_pages} pages")

            return StructuredDocument(
                filename=self.filename,
                title=title,
                elements=elements,
                total_pages=total_pages
            )
        except Exception as e:
            print(f"[DoclingLoader] Docling failed ({e}), falling back to PDFLoader")
            from loaders.pdf_loader import PDFLoader
            pdf_doc = PDFLoader(self.file_path).load()
            elements = [
                {
                    "type": "paragraph",
                    "content": page.get("text", ""),
                    "page": page.get("page_number", idx + 1),
                    "metadata": {
                        "source_file": self.filename,
                        "section": None,
                        "subsection": None,
                        "page": page.get("page_number", idx + 1),
                    },
                }
                for idx, page in enumerate(pdf_doc.pages)
                if page.get("text", "").strip()
            ]
            return StructuredDocument(
                filename=self.filename,
                title=None,
                elements=elements,
                total_pages=pdf_doc.total_pages
            )

    def _extract_structured_elements(self, doc: DoclingDocument) -> List[Dict[str, Any]]:
        elements = []
        current_section = None
        current_subsection = None
        figure_captions = {}
        table_captions = {}

        # PASS 1: Collect all captions first
        for item, _level in doc.iterate_items():
            label = getattr(item, 'label', None)
            text = getattr(item, 'text', '').strip()

            if label == DocItemLabel.CAPTION and text:
                page_num = self._get_page_number(item)
                if "Table" in text:
                    table_id = self._extract_id(text, ["Table"])
                    if table_id:
                        table_captions[table_id] = (text, page_num)
                elif "Figure" in text or "Fig." in text:
                    fig_id = self._extract_id(text, ["Figure", "Fig."])
                    if fig_id:
                        figure_captions[fig_id] = (text, page_num)

        # PASS 2: Extract all elements
        for item, _level in doc.iterate_items():
            element = self._process_doc_item(
                item, current_section, current_subsection,
                figure_captions, table_captions
            )
            if element:
                elements.append(element)
                if element["type"] == "heading":
                    level = element["metadata"].get("level", 1)
                    if level == 1:
                        current_section = element["content"]
                        current_subsection = None
                    elif level == 2:
                        current_subsection = element["content"]

        return elements

    def _process_doc_item(self, item, current_section, current_subsection,
                          figure_captions, table_captions):
        label = getattr(item, 'label', None)
        text = getattr(item, 'text', '').strip()

        if not text and label != DocItemLabel.TABLE:
            return None

        page_num = self._get_page_number(item)

        metadata = {
            "source_file": self.filename,
            "page": page_num,
            "section": current_section,
            "subsection": current_subsection,
            "document_type": "research_paper"
        }

        if label == DocItemLabel.TITLE:
            return {"type": "title", "content": text, "page": page_num, "metadata": metadata}

        elif label == DocItemLabel.SECTION_HEADER:
            metadata["level"] = 1
            return {"type": "heading", "content": text, "page": page_num, "metadata": metadata}

        elif label == DocItemLabel.PARAGRAPH:
            return {"type": "paragraph", "content": text, "page": page_num, "metadata": metadata}

        elif label == DocItemLabel.TABLE:
            # FIX 2: use markdown export for structured table content
            try:
                table_text = item.export_to_markdown()
            except Exception:
                table_text = text or "[Table content unavailable]"

            table_id = self._find_matching_id(table_captions, page_num)
            caption = table_captions[table_id][0] if table_id and table_id in table_captions else ""

            metadata["table_id"] = table_id or f"Table_p{page_num}"
            metadata["caption"] = caption
            metadata["has_caption"] = bool(caption)

            return {"type": "table", "content": table_text, "page": page_num, "metadata": metadata}

        elif label == DocItemLabel.PICTURE:
            figure_id = self._find_matching_id(figure_captions, page_num)
            caption = figure_captions[figure_id][0] if figure_id and figure_id in figure_captions else ""

            metadata["figure_id"] = figure_id or f"Figure_p{page_num}"
            metadata["caption"] = caption
            metadata["has_caption"] = bool(caption)

            return {"type": "figure", "content": text or "[Image content]", "page": page_num, "metadata": metadata}

        elif label == DocItemLabel.CAPTION:
            return {"type": "caption", "content": text, "page": page_num, "metadata": metadata}

        elif label == DocItemLabel.LIST_ITEM:
            return {"type": "list_item", "content": text, "page": page_num, "metadata": metadata}

        if not text:
            return None

        return {"type": "paragraph", "content": text, "page": page_num, "metadata": metadata}

    def _get_page_number(self, item: Any) -> int:
        # FIX 3: prov is a list in Docling
        try:
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                return getattr(prov, 'page_no', 1)
            return 1
        except:
            return 1

    def _get_total_pages(self, doc: DoclingDocument) -> int:
        try:
            pages = set()
            for item, _level in doc.iterate_items():
                pages.add(self._get_page_number(item))
            return len(pages) if pages else 1
        except:
            return 1

    def _extract_title(self, doc: DoclingDocument) -> Optional[str]:
        try:
        # First pass: look for TITLE label
            for item, _level in doc.iterate_items():
                if getattr(item, 'label', None) == DocItemLabel.TITLE:
                    return getattr(item, 'text', '').strip()
        
        # Fallback: use first SECTION_HEADER as title
            for item, _level in doc.iterate_items():
                if getattr(item, 'label', None) == DocItemLabel.SECTION_HEADER:
                    text = getattr(item, 'text', '').strip()
                    if text:
                        return text
            return None
        except:
            return None

    def _extract_id(self, text: str, prefixes: List[str]) -> Optional[str]:
        import re
        for prefix in prefixes:
            pattern = rf'{prefix}\s+(?:[IVX]+|\d+[a-z]?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _find_matching_id(self, captions: Dict[str, tuple], page_num: int) -> Optional[str]:
        # FIX 1: return closest caption, not just first match
        best_id = None
        best_distance = float('inf')
        for caption_id, (caption_text, cap_page) in captions.items():
            distance = abs(cap_page - page_num)
            if distance <= 1 and distance < best_distance:
                best_id = caption_id
                best_distance = distance
        return best_id

    def validate(self) -> bool:
        try:
            return os.path.exists(self.file_path) and self.file_path.lower().endswith('.pdf')
        except:
            return False