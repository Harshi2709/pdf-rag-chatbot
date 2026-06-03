"""
Text Chunking Module
Implements recursive character-based text splitting with overlap
"""
from typing import List, Dict, Any
import re


class TextChunk:
    """Represents a text chunk with metadata"""
    
    def __init__(self, text: str, metadata: Dict[str, Any], chunk_id: str):
        self.text = text
        self.metadata = metadata
        self.chunk_id = chunk_id
    
    def __repr__(self):
        return f"TextChunk(id={self.chunk_id}, length={len(self.text)})"


class RecursiveCharacterTextSplitter:
    """
    Recursive Character Text Splitter
    Splits text into chunks with configurable size and overlap
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize text splitter
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Separators in order of preference
        self.separators = ["\n\n", "\n", ". ", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using recursive separation
        
        Args:
            text: Input text to split
        
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        
        # Try each separator
        for separator in self.separators:
            if separator in text:
                splits = text.split(separator)
                current_chunk = ""
                
                for split in splits:
                    # If adding this split exceeds chunk size
                    if len(current_chunk) + len(split) + len(separator) > self.chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            # Start new chunk with overlap
                            overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                            current_chunk = overlap_text + separator + split
                        else:
                            current_chunk = split
                    else:
                        if current_chunk:
                            current_chunk += separator + split
                        else:
                            current_chunk = split
                
                # Add remaining chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                return chunks
        
        # Fallback: split by character count
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i:i + self.chunk_size])
        
        return chunks
    
    def create_chunks(self, pages: List[Dict[str, Any]]) -> List[TextChunk]:
        """
        Create chunks from PDF pages with metadata preservation
        
        Args:
            pages: List of page dictionaries from PDFDocument
        
        Returns:
            List of TextChunk objects
        """
        all_chunks = []
        chunk_counter = 0
        
        for page in pages:
            text = page["text"]
            page_number = page["page_number"]
            filename = page["filename"]
            
            # Split page text into chunks
            text_chunks = self.split_text(text)
            
            for chunk_text in text_chunks:
                chunk_id = f"{filename}_page{page_number}_chunk{chunk_counter}"
                
                metadata = {
                    "filename": filename,
                    "page": page_number,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_counter
                }
                
                chunk = TextChunk(
                    text=chunk_text,
                    metadata=metadata,
                    chunk_id=chunk_id
                )
                
                all_chunks.append(chunk)
                chunk_counter += 1
        
        return all_chunks
