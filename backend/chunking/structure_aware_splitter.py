"""
Structure-Aware Text Chunking
Respects document hierarchy, figures, tables, and section boundaries
"""
from importlib.metadata import metadata
from typing import List, Dict, Any
import re

class StructuredChunk:
    """Represents a structure-aware chunk with rich metadata"""
    
    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_id: str,
        chunk_type: str = "paragraph"
    ):
        self.text = text
        self.metadata = metadata
        self.chunk_id = chunk_id
        self.chunk_type = chunk_type  # paragraph, table, figure, heading
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id,
            "chunk_type": self.chunk_type
        }
    
    def __repr__(self):
        return f"StructuredChunk(id={self.chunk_id}, type={self.chunk_type}, length={len(self.text)})"


class StructureAwareSplitter:
    """
    Structure-Aware Document Chunking
    
    Respects:
    - Section boundaries
    - Figure captions (keeps figure + caption together)
    - Table captions (keeps table + caption together)
    - Heading hierarchy
    - Paragraph boundaries
    
    Avoids splitting:
    - Figures from captions
    - Tables from captions
    - Headings from their content
    """
    
    def __init__(
        self,
        max_chunk_size: int = 800,
        min_chunk_size: int = 100,
        respect_boundaries: bool = True
    ):
        """
        Initialize structure-aware splitter
        
        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk
            respect_boundaries: Whether to strictly respect element boundaries
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.respect_boundaries = respect_boundaries
    
    def create_chunks(self, elements: List[Dict[str, Any]]) -> List[StructuredChunk]:
        """
        Create structure-aware chunks from document elements
        
        Args:
            elements: List of structured elements from DoclingLoader
        
        Returns:
            List of StructuredChunk objects
        """
        chunks = []
        chunk_counter = 0
        
        # Group elements by page and section
        grouped_elements = self._group_elements(elements)
        
        for group in grouped_elements:
            group_chunks = self._process_group(group, chunk_counter)
            chunks.extend(group_chunks)
            chunk_counter += len(group_chunks)
        
        print(f"[StructureAwareSplitter] Created {len(chunks)} chunks")
        return chunks
    
    def _group_elements(self, elements: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group elements by logical boundaries
        
        Groups:
        - Figures with their captions
        - Tables with their captions
        - Headings with their paragraphs
        - Related paragraphs in same section
        """
        groups = []
        current_group = []
        current_section = None
        pending_caption = None
        
        for i, elem in enumerate(elements):
            elem_type = elem.get("type")
            section = elem.get("metadata", {}).get("section")
            
            # Handle captions
            if elem_type == "caption":
                pending_caption = elem
                continue
            
            # Handle figures
            if elem_type == "figure":
                figure_group = [elem]
                if pending_caption:
                    figure_group.insert(0, pending_caption)
                    pending_caption = None
                groups.append(figure_group)
                continue
            
            # Handle tables
            if elem_type == "table":
                table_group = [elem]
                if pending_caption:
                    table_group.insert(0, pending_caption)
                    pending_caption = None
                groups.append(table_group)
                continue
            
            # Handle headings
            if elem_type == "heading":
                # Flush current group
                if current_group:
                    groups.append(current_group)
                    current_group = []
                
                # Start new group with heading
                current_group = [elem]
                current_section = section
                continue
            
            # Handle paragraphs and other text
            if elem_type in ["paragraph", "list_item", "title"]:
                # Check if section changed
                if section != current_section and current_group:
                    groups.append(current_group)
                    current_group = []
                    current_section = section
                
                current_group.append(elem)
                
                # Flush if group is getting large
                group_size = sum(len(e.get("content", "")) for e in current_group)
                if group_size > self.max_chunk_size * 1.5:
                    groups.append(current_group)
                    current_group = []
        
        # Add remaining group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _process_group(
        self,
        group: List[Dict[str, Any]],
        start_counter: int
    ) -> List[StructuredChunk]:
        """Process a group of related elements into chunks"""
        chunks = []
        
        # Check group type
        has_figure = any(e.get("type") == "figure" for e in group)
        has_table = any(e.get("type") == "table" for e in group)
        
        # Handle figure groups
        if has_figure:
            chunk = self._create_figure_chunk(group, start_counter)
            if chunk:
                chunks.append(chunk)
            return chunks
        
        # Handle table groups
        if has_table:
            chunk = self._create_table_chunk(group, start_counter)
            if chunk:
                chunks.append(chunk)
            return chunks
        
        # Handle text groups (headings + paragraphs)
        text_chunks = self._create_text_chunks(group, start_counter)
        chunks.extend(text_chunks)
        
        return chunks
    
    def _create_figure_chunk(
        self,
        group: List[Dict[str, Any]],
        chunk_id: int
    ) -> StructuredChunk:
        """Create a chunk for a figure with its caption"""
        figure_elem = next((e for e in group if e.get("type") == "figure"), None)
        caption_elem = next((e for e in group if e.get("type") == "caption"), None)
        
        if not figure_elem:
            return None
        
        metadata = figure_elem.get("metadata", {}).copy()
        figure_id = metadata.get("figure_id", "Unknown")
        page = metadata.get("page", 1)
        
        # Build text
        text_parts = []
        
        if caption_elem:
            caption_text = caption_elem.get("content", "")
            text_parts.append(f"[FIGURE CAPTION] {caption_text}")
            metadata["caption"] = caption_text
        
        figure_content = figure_elem.get("content", "[Image content]")
        if figure_content and figure_content != "[Image content]":
            text_parts.append(f"[FIGURE CONTENT] {figure_content}")
        
        text = "\n\n".join(text_parts) if text_parts else f"[FIGURE] {figure_id}"
        
        chunk_id_str = f"figure_{figure_id.replace(' ', '_')}_{chunk_id}"
        
        return StructuredChunk(
            text=text,
            metadata=metadata,
            chunk_id=chunk_id_str,
            chunk_type="figure"
        )
    
    def _create_table_chunk(
        self,
        group: List[Dict[str, Any]],
        chunk_id: int
    ) -> StructuredChunk:
        table_elem = next((e for e in group if e.get("type") == "table"), None)
        caption_elem = next((e for e in group if e.get("type") == "caption"), None)

        if not table_elem:
            return None

        metadata = table_elem.get("metadata", {}).copy()
        table_id = metadata.get("table_id", "Unknown")
        text_parts = []

    # FIX: use caption_elem if present, else fall back to metadata caption
        caption_text = ""
        if caption_elem:
            caption_text = caption_elem.get("content", "")
        elif metadata.get("caption"):
            caption_text = metadata["caption"]  # ← already set by DoclingLoader

        if caption_text:
            text_parts.append(f"[TABLE CAPTION] {caption_text}")
            metadata["caption"] = caption_text
        table_content = table_elem.get("content", "")
        if table_content:
            text_parts.append(f"[TABLE CONTENT]\n{table_content}")

        text = "\n\n".join(text_parts) if text_parts else f"[TABLE] {table_id}"

        chunk_id_str = f"table_{table_id.replace(' ', '_')}_{chunk_id}"
        print(f"[DEBUG] Table chunk '{table_id}' size: {len(text)} chars")
        return StructuredChunk(
            text=text,
            metadata=metadata,
            chunk_id=chunk_id_str,
            chunk_type="table"
        )
    
    def _create_text_chunks(
        self,
        group: List[Dict[str, Any]],
        start_counter: int
    ) -> List[StructuredChunk]:
        """Create chunks from text elements (headings + paragraphs)"""
        chunks = []
        
        # Combine text from group
        combined_text = []
        base_metadata = None
        
        for elem in group:
            content = elem.get("content", "").strip()
            if not content:
                continue
            
            # Store base metadata from first element
            if base_metadata is None:
                base_metadata = elem.get("metadata", {}).copy()
            
            elem_type = elem.get("type")
            
            # Add type markers
            if elem_type == "heading":
                combined_text.append(f"\n## {content}\n")
            elif elem_type == "title":
                combined_text.append(f"\n# {content}\n")
            else:
                combined_text.append(content)
        
        full_text = "\n".join(combined_text).strip()
        
        if not full_text:
            return chunks
        
        # If text fits in one chunk, create single chunk
        if len(full_text) <= self.max_chunk_size:
            chunk_id_str = f"text_chunk_{start_counter}"
            chunk = StructuredChunk(
                text=full_text,
                metadata=base_metadata or {},
                chunk_id=chunk_id_str,
                chunk_type="paragraph"
            )
            chunks.append(chunk)
            return chunks
        
        # Split large text while respecting boundaries
        split_chunks = self._split_large_text(full_text, base_metadata, start_counter)
        chunks.extend(split_chunks)
        
        return chunks
    
    def _split_large_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        start_counter: int
    ) -> List[StructuredChunk]:
        """Split large text into smaller chunks at natural boundaries"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_counter = start_counter
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds max size
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_id_str = f"text_chunk_{chunk_counter}"
                    chunk = StructuredChunk(
                        text=current_chunk.strip(),
                        metadata=metadata.copy(),
                        chunk_id=chunk_id_str,
                        chunk_type="paragraph"
                    )
                    chunks.append(chunk)
                    chunk_counter += 1
                
                # Start new chunk
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add remaining chunk
        if current_chunk:
            chunk_id_str = f"text_chunk_{chunk_counter}"
            chunk = StructuredChunk(
                text=current_chunk.strip(),
                metadata=metadata.copy(),
                chunk_id=chunk_id_str,
                chunk_type="paragraph"
            )
            chunks.append(chunk)
        
        return chunks
