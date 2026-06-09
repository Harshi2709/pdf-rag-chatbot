"""
Docling-based PDF Loader
Structure-aware document parsing with figure and table extraction
"""
from typing import List, Dict, Any, Optional
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument, DocItemLabel
import os


class StructuredDocument:
    """Represents a structured document with hierarchy and metadata"""
    
    def __init__(
        self,
        filename: str,
        title: Optional[str],
        elements: List[Dict[str, Any]],
        total_pages: int
    ):
        self.filename = filename
        self.title = title
        self.elements = elements  # Structured elements (headings, paragraphs, tables, figures)
        self.total_pages = total_pages
    
    def get_elements_by_type(self, element_type: str) -> List[Dict[str, Any]]:
        """Filter elements by type"""
        return [elem for elem in self.elements if elem.get("type") == element_type]
    
    def get_figures(self) -> List[Dict[str, Any]]:
        """Get all figures"""
        return self.get_elements_by_type("figure")
    
    def get_tables(self) -> List[Dict[str, Any]]:
        """Get all tables"""
        return self.get_elements_by_type("table")
    
    def __repr__(self):
        return f"StructuredDocument(filename={self.filename}, elements={len(self.elements)}, pages={self.total_pages})"


class DoclingLoader:
    """
    Structure-aware PDF Loader using Docling
    
    Extracts:
    - Document hierarchy (headings, sections)
    - Paragraphs with section context
    - Tables with captions
    - Figures with captions
    - Page information
    - Layout structure
    """
    
    def __init__(self, file_path: str):
        """
        Initialize Docling Loader
        
        Args:
            file_path: Path to the PDF file
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.converter = DocumentConverter()
    
    def load(self) -> StructuredDocument:
        """
        Load and parse PDF with structure awareness
        
        Returns:
            StructuredDocument with hierarchical elements
        
        Raises:
            FileNotFoundError: If PDF doesn't exist
            Exception: If parsing fails
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        
        try:
            print(f"[DoclingLoader] Processing: {self.filename}")
            
            # Convert document
            result = self.converter.convert(self.file_path)
            doc: DoclingDocument = result.document
            
            # Extract structured elements
            elements = self._extract_structured_elements(doc)
            
            # Get total pages
            total_pages = self._get_total_pages(doc)
            
            # Extract title
            title = self._extract_title(doc)
            
            print(f"[DoclingLoader] Extracted {len(elements)} elements from {total_pages} pages")
            
            return StructuredDocument(
                filename=self.filename,
                title=title,
                elements=elements,
                total_pages=total_pages
            )
        
        except Exception as e:
            raise Exception(f"Failed to parse PDF with Docling: {str(e)}")
    
    def _extract_structured_elements(self, doc: DoclingDocument) -> List[Dict[str, Any]]:
        """
        Extract structured elements from DoclingDocument
        
        Returns list of element dictionaries with:
        - type: heading/paragraph/table/figure/caption
        - content: text content
        - page: page number
        - metadata: additional context (section, table_id, figure_id, etc.)
        """
        elements = []
        current_section = None
        current_subsection = None
        figure_captions = {}  # Store captions for figures
        table_captions = {}   # Store captions for tables
        
        # Iterate through document items
        for item in doc.iterate_items():
            element = self._process_doc_item(
                item,
                current_section,
                current_subsection,
                figure_captions,
                table_captions
            )
            
            if element:
                elements.append(element)
                
                # Update section tracking
                if element["type"] == "heading":
                    level = element["metadata"].get("level", 1)
                    if level == 1:
                        current_section = element["content"]
                        current_subsection = None
                    elif level == 2:
                        current_subsection = element["content"]
                
                # Store captions for later association
                elif element["type"] == "caption":
                    caption_text = element["content"]
                    if "Figure" in caption_text or "Fig." in caption_text:
                        fig_id = self._extract_id(caption_text, ["Figure", "Fig."])
                        if fig_id:
                            figure_captions[fig_id] = caption_text
                    elif "Table" in caption_text:
                        table_id = self._extract_id(caption_text, ["Table"])
                        if table_id:
                            table_captions[table_id] = caption_text
        
        return elements
    
    def _process_doc_item(
        self,
        item: Any,
        current_section: Optional[str],
        current_subsection: Optional[str],
        figure_captions: Dict[str, str],
        table_captions: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Process a single document item"""
        
        # Get basic properties
        label = getattr(item, 'label', None)
        text = getattr(item, 'text', '').strip()
        
        if not text:
            return None
        
        # Get page number
        page_num = self._get_page_number(item)
        
        # Base metadata
        metadata = {
            "source_file": self.filename,
            "page": page_num,
            "section": current_section,
            "subsection": current_subsection,
            "document_type": "research_paper"
        }
        
        # Process based on label type
        if label == DocItemLabel.TITLE:
            return {
                "type": "title",
                "content": text,
                "page": page_num,
                "metadata": metadata
            }
        
        elif label == DocItemLabel.SECTION_HEADER:
            metadata["level"] = 1
            return {
                "type": "heading",
                "content": text,
                "page": page_num,
                "metadata": metadata
            }
        
        elif label == DocItemLabel.PARAGRAPH:
            return {
                "type": "paragraph",
                "content": text,
                "page": page_num,
                "metadata": metadata
            }
        
        elif label == DocItemLabel.TABLE:
            # Extract table ID from nearby caption
            table_id = self._find_matching_id(table_captions, page_num)
            caption = table_captions.get(table_id, "")
            
            metadata["table_id"] = table_id or f"Table_p{page_num}"
            metadata["caption"] = caption
            metadata["has_caption"] = bool(caption)
            
            return {
                "type": "table",
                "content": text,
                "page": page_num,
                "metadata": metadata
            }
        
        elif label == DocItemLabel.PICTURE:
            # Extract figure ID from nearby caption
            figure_id = self._find_matching_id(figure_captions, page_num)
            caption = figure_captions.get(figure_id, "")
            
            metadata["figure_id"] = figure_id or f"Figure_p{page_num}"
            metadata["caption"] = caption
            metadata["has_caption"] = bool(caption)
            
            return {
                "type": "figure",
                "content": text or "[Image content]",
                "page": page_num,
                "metadata": metadata
            }
        
        elif label == DocItemLabel.CAPTION:
            return {
                "type": "caption",
                "content": text,
                "page": page_num,
                "metadata": metadata
            }
        
        elif label == DocItemLabel.LIST_ITEM:
            return {
                "type": "list_item",
                "content": text,
                "page": page_num,
                "metadata": metadata
            }
        
        # Default: treat as paragraph
        return {
            "type": "paragraph",
            "content": text,
            "page": page_num,
            "metadata": metadata
        }
    
    def _get_page_number(self, item: Any) -> int:
        """Extract page number from document item"""
        try:
            if hasattr(item, 'prov') and hasattr(item.prov, 'page_no'):
                return item.prov.page_no
            return 1
        except:
            return 1
    
    def _get_total_pages(self, doc: DoclingDocument) -> int:
        """Get total page count"""
        try:
            pages = set()
            for item in doc.iterate_items():
                page_num = self._get_page_number(item)
                pages.add(page_num)
            return len(pages) if pages else 1
        except:
            return 1
    
    def _extract_title(self, doc: DoclingDocument) -> Optional[str]:
        """Extract document title"""
        try:
            for item in doc.iterate_items():
                if getattr(item, 'label', None) == DocItemLabel.TITLE:
                    return getattr(item, 'text', '').strip()
            return None
        except:
            return None
    
    def _extract_id(self, text: str, prefixes: List[str]) -> Optional[str]:
        """Extract ID from caption text (e.g., 'Figure 4' -> 'Figure 4')"""
        import re
        for prefix in prefixes:
            # Match patterns like "Figure 4", "Fig. 2", "Table I", "Table II"
            pattern = rf'{prefix}\s+(?:[IVX]+|\d+[a-z]?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _find_matching_id(self, captions: Dict[str, str], page_num: int) -> Optional[str]:
        """Find matching caption ID for an element on a given page"""
        # Simple heuristic: return any caption ID found on the same page
        # In production, you'd use spatial proximity
        for caption_id in captions:
            return caption_id
        return None
    
    def validate(self) -> bool:
        """Validate if file is a valid PDF"""
        try:
            if not os.path.exists(self.file_path):
                return False
            if not self.file_path.lower().endswith('.pdf'):
                return False
            return True
        except:
            return False
