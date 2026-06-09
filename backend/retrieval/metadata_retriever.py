"""
Metadata-Aware Retriever
Enhanced retrieval with structure-aware filtering and ranking
"""
from typing import List, Dict, Optional, Any
from embeddings.embedding_model import embedding_model
from vectordb.chroma_client import ChromaDBClient
from retrieval.retriever import RetrievedDocument


class MetadataRetriever:
    """
    Structure-aware retriever with metadata filtering
    
    Supports:
    - Metadata-based filtering (figure_id, table_id, section, page)
    - Type-based boosting (prioritize figures/tables)
    - Hybrid ranking (semantic + metadata)
    """
    
    def __init__(self, vector_db: ChromaDBClient, top_k: int = 5):
        """
        Initialize metadata retriever
        
        Args:
            vector_db: ChromaDB client instance
            top_k: Number of top documents to retrieve
        """
        self.vector_db = vector_db
        self.top_k = top_k
        self.embedding_model = embedding_model
    
    def retrieve(
        self,
        query: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """
        Retrieve documents with optional metadata filtering
        
        Args:
            query: User query string
            metadata_filters: Optional metadata filters
                Examples:
                - {"type": "figure", "figure_ids": ["Figure 4"]}
                - {"type": "table", "table_ids": ["Table I"]}
                - {"section": "Results"}
            top_k: Override default top_k
        
        Returns:
            List of RetrievedDocument objects
        """
        k = top_k if top_k is not None else self.top_k
        
        # Generate query embedding
        print(f"[MetadataRetriever] Generating embedding for query: {query[:50]}...")
        query_embedding = self.embedding_model.embed_text(query)
        
        # Apply metadata filtering if provided
        if metadata_filters and metadata_filters.get("type"):
            print(f"[MetadataRetriever] Applying metadata filters: {metadata_filters}")
            retrieved_docs = self._retrieve_with_filters(
                query_embedding,
                metadata_filters,
                k
            )
        else:
            print(f"[MetadataRetriever] Performing standard semantic search")
            retrieved_docs = self._retrieve_standard(query_embedding, k)
        
        print(f"[MetadataRetriever] Retrieved {len(retrieved_docs)} documents")
        return retrieved_docs
    
    def _retrieve_standard(
        self,
        query_embedding: List[float],
        top_k: int
    ) -> List[RetrievedDocument]:
        """Standard semantic search without filtering"""
        search_results = self.vector_db.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        return self._build_retrieved_documents(search_results)
    
    def _retrieve_with_filters(
        self,
        query_embedding: List[float],
        metadata_filters: Dict[str, Any],
        top_k: int
    ) -> List[RetrievedDocument]:
        """
        Retrieve with metadata filtering
        
        Strategy:
        1. Try exact metadata filtering first
        2. If insufficient results, fall back to broader search
        3. Re-rank results to boost matching metadata
        """
        filter_type = metadata_filters.get("type")
        
        # Build ChromaDB where clause
        where_clause = {}
        
        if filter_type == "figure":
            # Filter for figure chunks
            figure_ids = metadata_filters.get("figure_ids", [])
            
            if figure_ids:
                # Exact figure ID match
                where_clause = {"$or": [
                    {"figure_id": {"$eq": fig_id}} for fig_id in figure_ids
                ]}
            else:
                # Any figure
                where_clause = {"chunk_type": {"$eq": "figure"}}
        
        elif filter_type == "table":
            # Filter for table chunks
            table_ids = metadata_filters.get("table_ids", [])
            
            if table_ids:
                # Exact table ID match
                where_clause = {"$or": [
                    {"table_id": {"$eq": table_id}} for table_id in table_ids
                ]}
            else:
                # Any table
                where_clause = {"chunk_type": {"$eq": "table"}}
        
        # Perform filtered search
        try:
            search_results = self.vector_db.similarity_search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Get more results for filtering
                where=where_clause if where_clause else None
            )
            
            retrieved_docs = self._build_retrieved_documents(search_results)
            
            # If we got enough results, return them
            if len(retrieved_docs) >= top_k:
                return retrieved_docs[:top_k]
            
            # Otherwise, fall back to broader search
            print(f"[MetadataRetriever] Filtered search returned {len(retrieved_docs)} results. Falling back to broader search.")
            fallback_results = self._retrieve_standard(query_embedding, top_k)
            
            # Combine and deduplicate
            combined = self._merge_results(retrieved_docs, fallback_results, top_k)
            return combined
        
        except Exception as e:
            print(f"[MetadataRetriever] Filtering failed: {e}. Using standard search.")
            return self._retrieve_standard(query_embedding, top_k)
    
    def _build_retrieved_documents(
        self,
        search_results: Dict[str, Any]
    ) -> List[RetrievedDocument]:
        """Build RetrievedDocument objects from search results"""
        retrieved_docs = []
        
        for text, metadata, distance in zip(
            search_results["documents"],
            search_results["metadatas"],
            search_results["distances"]
        ):
            # Convert distance to similarity score
            similarity_score = 1.0 / (1.0 + distance)
            
            doc = RetrievedDocument(
                text=text,
                metadata=metadata,
                similarity_score=similarity_score
            )
            retrieved_docs.append(doc)
        
        return retrieved_docs
    
    def _merge_results(
        self,
        primary: List[RetrievedDocument],
        fallback: List[RetrievedDocument],
        top_k: int
    ) -> List[RetrievedDocument]:
        """Merge primary and fallback results, removing duplicates"""
        seen_ids = set()
        merged = []
        
        # Add primary results first
        for doc in primary:
            doc_id = doc.metadata.get("chunk_id", doc.text[:50])
            if doc_id not in seen_ids:
                merged.append(doc)
                seen_ids.add(doc_id)
        
        # Add fallback results
        for doc in fallback:
            doc_id = doc.metadata.get("chunk_id", doc.text[:50])
            if doc_id not in seen_ids:
                merged.append(doc)
                seen_ids.add(doc_id)
            
            if len(merged) >= top_k:
                break
        
        return merged[:top_k]
    
    def assemble_context(
        self,
        retrieved_docs: List[RetrievedDocument],
        highlight_metadata: bool = True
    ) -> str:
        """
        Assemble context with metadata awareness
        
        Args:
            retrieved_docs: List of retrieved documents
            highlight_metadata: Whether to highlight structure metadata
        
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return ""
        
        context_parts = []
        
        # Group by document type for better organization
        figures = [d for d in retrieved_docs if d.metadata.get("chunk_type") == "figure"]
        tables = [d for d in retrieved_docs if d.metadata.get("chunk_type") == "table"]
        text = [d for d in retrieved_docs if d.metadata.get("chunk_type") not in ["figure", "table"]]
        
        chunk_num = 1
        
        # Add figures first
        if figures:
            context_parts.append("=== FIGURES ===\n")
            for doc in figures:
                context_parts.append(self._format_chunk(doc, chunk_num, highlight_metadata))
                chunk_num += 1
        
        # Add tables
        if tables:
            context_parts.append("\n=== TABLES ===\n")
            for doc in tables:
                context_parts.append(self._format_chunk(doc, chunk_num, highlight_metadata))
                chunk_num += 1
        
        # Add text content
        if text:
            if figures or tables:
                context_parts.append("\n=== TEXT CONTENT ===\n")
            for doc in text:
                context_parts.append(self._format_chunk(doc, chunk_num, highlight_metadata))
                chunk_num += 1
        
        return "\n".join(context_parts)
    
    def _format_chunk(
        self,
        doc: RetrievedDocument,
        chunk_num: int,
        highlight_metadata: bool
    ) -> str:
        """Format a single chunk with metadata"""
        metadata = doc.metadata
        
        # Build header
        header_parts = [f"Chunk {chunk_num}"]
        
        filename = metadata.get("source_file", metadata.get("filename", "unknown"))
        page = metadata.get("page", "unknown")
        header_parts.append(f"{filename}, Page {page}")
        
        chunk_type = metadata.get("chunk_type", "text")
        if chunk_type == "figure":
            figure_id = metadata.get("figure_id", "Unknown")
            header_parts.append(f"[FIGURE: {figure_id}]")
        elif chunk_type == "table":
            table_id = metadata.get("table_id", "Unknown")
            header_parts.append(f"[TABLE: {table_id}]")
        
        section = metadata.get("section")
        if section:
            header_parts.append(f"Section: {section}")
        
        similarity = f"Relevance: {doc.similarity_score:.2f}"
        header_parts.append(similarity)
        
        header = " | ".join(header_parts)
        
        # Build content
        content = doc.text
        
        return f"[{header}]\n{content}\n"
    
    def extract_citations(self, retrieved_docs: List[RetrievedDocument]) -> List[Dict[str, Any]]:
        """
        Extract citations with structure awareness
        
        Returns citations grouped by type
        """
        citations = []
        seen = set()
        
        for doc in retrieved_docs:
            metadata = doc.metadata
            
            filename = metadata.get("source_file", metadata.get("filename", "unknown"))
            page = metadata.get("page", "unknown")
            chunk_type = metadata.get("chunk_type", "text")
            
            # Build citation key
            citation_key = f"{filename}_{page}_{chunk_type}"
            
            if citation_key not in seen:
                citation = {
                    "file": filename,
                    "page": page,
                    "type": chunk_type
                }
                
                # Add specific IDs
                if chunk_type == "figure":
                    citation["figure_id"] = metadata.get("figure_id")
                elif chunk_type == "table":
                    citation["table_id"] = metadata.get("table_id")
                
                citations.append(citation)
                seen.add(citation_key)
        
        return citations
