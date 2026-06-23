"""
Unified document loader for V1 PDF and DOCX ingestion.
Supports PDF and DOCX files.
"""
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import docx  # type: ignore
except Exception:  # pragma: no cover
    docx = None

from loaders.docling_loader import DoclingLoader
from loaders.pdf_loader import PDFLoader
from loaders.office_loader import load_docx


class DocumentLoader:
    """Simple unified loader for the existing V1 RAG path."""

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx"
    }

    @staticmethod
    def compute_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def detect_file_type(file_path: str) -> str:
        return Path(file_path).suffix.lower().lstrip(".") or "unknown"

    @classmethod
    def extract_pages(cls, file_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        file_type = cls.detect_file_type(file_path)
        filename = os.path.basename(file_path)
        document_hash = cls.compute_hash(file_path)

        if file_type == "pdf":
            try:
                doc = DoclingLoader(file_path).load()
                elements = doc.elements
            except Exception:
                elements = PDFLoader(file_path).load().pages

            for el in elements:
                el.setdefault("metadata", {})
                el["metadata"].update({
                    "document_hash": document_hash,
                    "file_type": file_type,
                    "filename": filename,
                    "source_file": filename,
                })
            return elements

        if file_type == "docx":
            raw_elements = load_docx(file_path)
            elements = [
                {
                    "page_number": el.get("page", 1),
                    "text": el.get("content", ""),
                    "filename": filename,
                    "metadata": el.get("metadata", {}),
                }
                for el in raw_elements
            ]
        else:
            elements = None

        if elements is not None:
            for el in elements:
                el.setdefault("metadata", {})
                el["metadata"].update({
                    "document_hash": document_hash,
                    "file_type": file_type,
                    "filename": filename,
                })
            return elements

        raise ValueError(f"Unsupported file type: {file_type}")

