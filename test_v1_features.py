import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from loaders.document_loader import DocumentLoader
from retrieval.retriever import Retriever
from vectordb.chroma_client import ChromaDBClient


def test_document_loader_supports_multi_format_extensions():
    assert ".pdf" in DocumentLoader.SUPPORTED_EXTENSIONS
    assert ".docx" in DocumentLoader.SUPPORTED_EXTENSIONS


def test_context_compression_truncates_long_context():
    retriever = Retriever.__new__(Retriever)
    retriever.top_k = 3
    huge_text = "word " * 500
    compressed = retriever.compress_context(huge_text, max_chars=120)
    assert len(compressed) <= 123


def test_document_hash_works_for_existing_file():
    sample_path = os.path.join("backend", "requirements.txt")
    digest = DocumentLoader.compute_hash(sample_path)
    assert isinstance(digest, str) and len(digest) == 64
