"""
PDF Loader Module
Handles PDF document loading with metadata preservation
"""
from typing import List, Dict, Any
from pypdf import PdfReader
import os


class PDFDocument:
    """Represents a loaded PDF document with metadata"""
    
    def __init__(self, filename: str, pages: List[Dict[str, Any]]):
        self.filename = filename
        self.pages = pages
        self.total_pages = len(pages)
    
    def __repr__(self):
        return f"PDFDocument(filename={self.filename}, pages={self.total_pages})"


class PDFLoader:
    """
    PDF Loader that extracts text and preserves metadata
    Uses PyPDF for document parsing
    """
    
    def __init__(self, file_path: str):
        """
        Initialize PDF Loader
        
        Args:
            file_path: Path to the PDF file
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
    
    def load(self) -> PDFDocument:
        """
        Load PDF and extract text with metadata
        
        Returns:
            PDFDocument object containing pages and metadata
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF parsing fails
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        
        try:
            reader = PdfReader(self.file_path)
            pages = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                page_data: Dict[str, Any] = {
                    "page_number": page_num,
                    "text": text,
                    "filename": self.filename,
                    "metadata": {
                        "source": self.file_path,
                        "page": page_num,
                        "total_pages": len(reader.pages)
                    }
                }
                pages.append(page_data)
            
            return PDFDocument(filename=self.filename, pages=pages)
        
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def validate(self) -> bool:
        """
        Validate if file is a valid PDF
        
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            reader = PdfReader(self.file_path)
            return len(reader.pages) > 0
        except:
            return False
