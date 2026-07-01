"""
Structure-Aware RAG Pipeline
Enhanced RAG workflow with document structure understanding
"""
import os
import time
from typing import Dict, List, Any
from loaders.document_loader import DocumentLoader
from loaders.docling_loader import DoclingLoader, StructuredDocument
from chunking.structure_aware_splitter import StructureAwareSplitter
from embeddings.embedding_model import embedding_model
from vectordb.chroma_client import ChromaDBClient
from retrieval.metadata_retriever import MetadataRetriever
from services.query_router import QueryRouter
from llm.ollama_client import OllamaClient
from prompts.rag_prompt import RAGPromptTemplate
from utils.logging_config import get_logger
from services.figure_describer import FigureDescriber

logger = get_logger(__name__)


class StructureAwareRAGPipeline:
    """
    Structure-Aware RAG Pipeline
    
    Enhancements:
    - Docling-based PDF parsing
    - Structure-aware chunking
    - Figure/Table extraction
    - Metadata-aware retrieval
    - Query routing for figures/tables
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        top_k: int = 5,
        model_name: str = "llama3"
    ):
        """
        Initialize Structure-Aware RAG Pipeline
        
        Args:
            chunk_size: Maximum size of text chunks
            top_k: Number of documents to retrieve
            model_name: Ollama model name
        """
        self.chunk_size = chunk_size
        self.top_k = top_k
        
        # Initialize new components
        self.structure_splitter = StructureAwareSplitter(
            max_chunk_size=chunk_size,
            min_chunk_size=100
        )
        self.embedding_model = embedding_model
        self.vector_db = ChromaDBClient()
        self.metadata_retriever = MetadataRetriever(
            vector_db=self.vector_db,
            top_k=top_k
        )
        self.query_router = QueryRouter()
        self.llm_client = OllamaClient(model_name=model_name)
        self.prompt_template = RAGPromptTemplate()
    
    def ingest_document(self, file_path: str, upload_timestamp: str = None) -> Dict[str, Any]:
        """
        Structure-aware PDF ingestion pipeline
        
        Pipeline stages:
        1. Docling PDF Loading (structure extraction)
        2. Structure-Aware Chunking
        3. Embedding Generation
        4. Vector Storage with Metadata
        
        Args:
            file_path: Path to PDF file
            upload_timestamp: Timestamp of upload
        
        Returns:
            Ingestion status dictionary with structure metrics
        """
        start_time = time.time()
        
        try:
            # Stage 1: Structure-Aware loading (PDF via Docling, other formats via unified loader)
            logger.info("=== Stage 1: Loading document ===")
            if DocumentLoader.detect_file_type(file_path) == 'pdf':
                loader = DoclingLoader(file_path)
                structured_doc: StructuredDocument = loader.load()
                # Enrich figure elements with LLaVA descriptions
                structured_doc.elements = self._enrich_figures(
                    structured_doc.elements, file_path
                )
                pages = structured_doc.elements
            else:
                pages = DocumentLoader.extract_pages(file_path)
                structured_doc = None
            
            filename = structured_doc.filename if structured_doc else os.path.basename(file_path)
            logger.info("Loaded: %s", filename)
            if structured_doc:
                logger.debug("Document details - pages: %s, title: %s, elements: %s, figures: %s, tables: %s",
                             structured_doc.total_pages,
                             structured_doc.title or 'N/A',
                             len(structured_doc.elements),
                             len(structured_doc.get_figures()),
                             len(structured_doc.get_tables()))
            else:
                logger.debug("Document details - pages: %s", len(pages))
            
            # Stage 2: Structure-Aware Chunking
            logger.info("=== Stage 2: Structure-Aware Chunking ===")
            chunks = self.structure_splitter.create_chunks(pages if not structured_doc else structured_doc.elements)
            
            # Count chunk types
            chunk_types = {}
            for chunk in chunks:
                chunk_type = chunk.chunk_type
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            logger.info("Created %d chunks", len(chunks))
            for chunk_type, count in chunk_types.items():
                logger.debug("Chunk type %s: %d", chunk_type, count)
            
            # Stage 3: Embedding Generation
            logger.info("=== Stage 3: Generating Embeddings ===")
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_model.embed_texts(texts)
            logger.info("Generated %d embeddings", len(embeddings))
            
            # Stage 4: Vector Storage with Metadata
            logger.info("=== Stage 4: Storing with Metadata ===")
            
            if upload_timestamp is None:
                from datetime import datetime
                upload_timestamp = datetime.now().isoformat()
            
            # Enrich metadata
            metadatas = []
            for chunk in chunks:
                metadata = chunk.metadata.copy()
                metadata["upload_timestamp"] = upload_timestamp
                metadata["chunk_type"] = getattr(chunk, 'chunk_type', 'text')
                metadata.setdefault("filename", filename)
                metadata.setdefault("file_type", DocumentLoader.detect_file_type(file_path))
                metadata.setdefault("document_hash", DocumentLoader.compute_hash(file_path))
                metadata.setdefault("document_id", f"doc_{metadata['document_hash'][:12]}")
                metadatas.append(metadata)
            
            ids = [chunk.chunk_id for chunk in chunks]
            
            # Store in vector DB
            self.vector_db.add_documents(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            processing_time = time.time() - start_time
            logger.info("Ingestion complete in %.2fs", processing_time)
            
            return {
                "status": "success",
                "filename": filename,
                "total_pages": structured_doc.total_pages if structured_doc else len(pages),
                "total_chunks": len(chunks),
                "chunk_breakdown": chunk_types,
                "figures_extracted": len(structured_doc.get_figures()) if structured_doc else 0,
                "tables_extracted": len(structured_doc.get_tables()) if structured_doc else 0,
                "vector_db_count": self.vector_db.get_collection_count(),
                "processing_time": f"{processing_time:.2f}s",
                "upload_timestamp": upload_timestamp,
                "document_title": structured_doc.title if structured_doc else None
            }
        
        except Exception as e:
            logger.exception("Error ingesting document %s", file_path)
            return {
                "status": "error",
                "error": str(e),
                "processing_time": f"{time.time() - start_time:.2f}s"
            }
    
    def ingest_pdf(self, file_path: str, upload_timestamp: str = None) -> Dict[str, Any]:
        """Backward-compatible alias for document ingestion."""
        return self.ingest_document(file_path, upload_timestamp)

    def _enrich_figures(self, elements: List[Dict[str, Any]], pdf_path: str) -> List[Dict[str, Any]]:
        """
        Replace '[Image content]' placeholders in figure elements
        with LLaVA-generated descriptions.
        Only runs if LLaVA is available in Ollama.
        """
        figure_elements = [e for e in elements if e.get("type") == "figure"]

        if not figure_elements:
            logger.info("[RAGPipeline] No figures found, skipping enrichment")
            return elements

        describer = FigureDescriber(pdf_path)

        if not describer.is_llava_available():
            logger.warning(
                "[RAGPipeline] LLaVA not available — figures will not be described. "
                "Run: ollama pull llava"
            )
            return elements

        logger.info(f"[RAGPipeline] Enriching {len(figure_elements)} figure(s) with LLaVA...")

        # Track figure index per page (handles multiple figures on same page)
        page_figure_counter: Dict[int, int] = {}

        for elem in elements:
            if elem.get("type") != "figure":
                continue

            page = elem.get("page", 1)
            fig_index = page_figure_counter.get(page, 0)
            page_figure_counter[page] = fig_index + 1

            figure_id = elem.get("metadata", {}).get("figure_id", f"Figure_p{page}")
            caption = elem.get("metadata", {}).get("caption", "")

            logger.info(f"[RAGPipeline] Describing {figure_id} (page {page}, index {fig_index})...")
            description = describer.describe_figure_on_page(page, fig_index)

            if description:
                enriched = f"[FIGURE: {figure_id}]"
                if caption:
                    enriched += f"\n[CAPTION] {caption}"
                enriched += f"\n[DESCRIPTION] {description}"
                elem["content"] = enriched
                elem["metadata"]["has_visual_description"] = True
                logger.info(f"[RAGPipeline] ✓ {figure_id} described successfully")
            else:
                # Fallback: at least preserve caption if available
                if caption:
                    elem["content"] = f"[FIGURE: {figure_id}]\n[CAPTION] {caption}"
                elem["metadata"]["has_visual_description"] = False
                logger.warning(f"[RAGPipeline] ✗ {figure_id} — LLaVA returned nothing, using caption fallback")

        describer.close()
        logger.info("[RAGPipeline] Figure enrichment complete")
        return elements
    
    def query(self, question: str, debug: bool = False) -> Dict[str, Any]:
        """
        Structure-aware RAG query pipeline
        
        Pipeline stages:
        1. Query Routing (detect figures/tables)
        2. Metadata-Aware Retrieval
        3. Context Assembly
        4. Prompt Construction
        5. LLM Inference
        
        Args:
            question: User question
            debug: Include debug information
        
        Returns:
            Response dictionary with answer and metadata
        """
        start_time = time.time()
        
        try:
            # Stage 1: Query Routing
            logger.info("=== Stage 1: Query Routing ===")
            routing_result = self.query_router.route_query(question)
            
            logger.info("Query Type: %s", routing_result['query_type'])
            logger.debug("Routing Strategy: %s", routing_result['routing_strategy'])
            if routing_result.get('detected_entities'):
                logger.debug("Detected Entities: %s", routing_result['detected_entities'])
            
            # Stage 2: Metadata-Aware Retrieval
            logger.info("=== Stage 2: Metadata-Aware Retrieval ===")
            metadata_filters = routing_result.get('metadata_filters')
            
            retrieved_docs = self.metadata_retriever.retrieve(
                query=question,
                metadata_filters=metadata_filters,
                top_k=self.top_k
            )
            
            logger.info("Retrieved %d documents", len(retrieved_docs))
            
            # Stage 3: Context Assembly
            logger.info("=== Stage 3: Assembling Context ===")
            context = self.metadata_retriever.assemble_context(
                retrieved_docs,
                highlight_metadata=True
            )
            
            # Stage 4: Prompt Construction
            logger.info("=== Stage 4: Building Prompt ===")
            prompt = self.prompt_template.build_prompt(context, question)
            
            # Stage 5: LLM Inference
            logger.info("=== Stage 5: Generating Response ===")
            answer = self.llm_client.generate(prompt, temperature=0.7)
            
            # Extract citations
            citations = self.metadata_retriever.extract_citations(retrieved_docs)
            
            processing_time = time.time() - start_time
            logger.info("Query complete in %.2fs", processing_time)
            
            avg_similarity = sum(doc.similarity_score for doc in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0.0
            confidence = round(min(0.99, 0.35 + 0.35 * min(1.0, len(citations) / 5.0) + 0.30 * avg_similarity), 2)

            response = {
                "answer": answer.strip(),
                "citations": citations,
                "sources": citations,
                "confidence": confidence,
                "retrieved_chunks": [doc.to_dict() for doc in retrieved_docs],
                "processing_time": f"{processing_time:.2f}s",
                "metadata": {
                    "num_chunks_retrieved": len(retrieved_docs),
                    "model": self.llm_client.model_name,
                    "query_type": routing_result['query_type']
                }
            }
            
            # Add debug info if requested
            if debug:
                response["debug_info"] = {
                    "query_routing": routing_result,
                    "metadata_filters_applied": metadata_filters,
                    "chunk_types_retrieved": [
                        doc.metadata.get("chunk_type", "unknown")
                        for doc in retrieved_docs
                    ]
                }
            
            return response
        
        except Exception as e:
            logger.exception("Error processing query: %s", question)
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "retrieved_chunks": [],
                "processing_time": f"{time.time() - start_time:.2f}s",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "vector_db_count": self.vector_db.get_collection_count(),
            "chunk_size": self.chunk_size,
            "top_k": self.top_k,
            "model": self.llm_client.model_name,
            "ollama_available": self.llm_client.check_availability(),
            "documents": self.vector_db.get_all_documents(),
            "pipeline_type": "structure_aware"
        }
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of all uploaded documents"""
        return self.vector_db.get_all_documents()
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """Delete a specific document"""
        try:
            success = self.vector_db.delete_document(filename)
            if success:
                return {
                    "status": "success",
                    "message": f"Document '{filename}' deleted successfully",
                    "vector_db_count": self.vector_db.get_collection_count()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Document '{filename}' not found"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def clear_all_documents(self) -> Dict[str, Any]:
        """Clear all documents"""
        try:
            self.vector_db.reset_collection()
            return {
                "status": "success",
                "message": "All documents cleared successfully",
                "vector_db_count": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
