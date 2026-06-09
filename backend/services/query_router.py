"""
Query Router for Structure-Aware Retrieval
Detects figure/table references and applies metadata filtering
"""
import re
from typing import Dict, Any, Optional, List


class QueryRouter:
    """
    Routes queries to appropriate retrieval strategies based on content
    
    Detects:
    - Figure references (e.g., "Figure 4", "Fig. 2")
    - Table references (e.g., "Table I", "Table II")
    - Section queries
    - General semantic queries
    """
    
    def __init__(self):
        # Patterns for figure detection
        self.figure_patterns = [
            r'\bFigure\s+(\d+[a-z]?)\b',  # Figure 4, Figure 4a
            r'\bFig\.\s*(\d+[a-z]?)\b',    # Fig. 4, Fig.4
            r'\bFigure\s+([IVX]+)\b',      # Figure IV (Roman numerals)
        ]
        
        # Patterns for table detection
        self.table_patterns = [
            r'\bTable\s+(\d+[a-z]?)\b',    # Table 1, Table 2a
            r'\bTable\s+([IVX]+)\b',       # Table I, Table II (Roman numerals)
        ]
        
        # Keywords for figure queries
        self.figure_keywords = [
            'figure', 'fig', 'diagram', 'illustration',
            'image', 'chart', 'graph', 'visualization', 'shown in'
        ]
        
        # Keywords for table queries
        self.table_keywords = [
            'table', 'values', 'results', 'data',
            'comparison', 'metrics', 'performance', 'accuracy'
        ]
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query and determine retrieval strategy
        
        Args:
            query: User query string
        
        Returns:
            Dictionary with:
            - query_type: "figure", "table", "section", or "general"
            - metadata_filters: Dictionary of filters to apply
            - detected_entities: List of detected figure/table IDs
            - routing_strategy: Description of routing decision
        """
        query_lower = query.lower()
        
        # Check for figure references
        figure_ids = self._extract_figure_ids(query)
        if figure_ids:
            return {
                "query_type": "figure",
                "metadata_filters": {
                    "type": "figure",
                    "figure_ids": figure_ids
                },
                "detected_entities": figure_ids,
                "routing_strategy": f"Detected figure reference(s): {', '.join(figure_ids)}. Will prioritize figure chunks.",
                "should_filter": True
            }
        
        # Check for table references
        table_ids = self._extract_table_ids(query)
        if table_ids:
            return {
                "query_type": "table",
                "metadata_filters": {
                    "type": "table",
                    "table_ids": table_ids
                },
                "detected_entities": table_ids,
                "routing_strategy": f"Detected table reference(s): {', '.join(table_ids)}. Will prioritize table chunks.",
                "should_filter": True
            }
        
        # Check for figure-related keywords (without specific ID)
        if any(keyword in query_lower for keyword in self.figure_keywords):
            return {
                "query_type": "figure_general",
                "metadata_filters": {
                    "type": "figure"
                },
                "detected_entities": [],
                "routing_strategy": "Detected figure-related query. Will boost figure chunks in results.",
                "should_filter": False  # Don't filter, just boost
            }
        
        # Check for table-related keywords (without specific ID)
        if any(keyword in query_lower for keyword in self.table_keywords):
            return {
                "query_type": "table_general",
                "metadata_filters": {
                    "type": "table"
                },
                "detected_entities": [],
                "routing_strategy": "Detected table-related query. Will boost table chunks in results.",
                "should_filter": False  # Don't filter, just boost
            }
        
        # Default: general semantic search
        return {
            "query_type": "general",
            "metadata_filters": {},
            "detected_entities": [],
            "routing_strategy": "General semantic search across all document types.",
            "should_filter": False
        }
    
    def _extract_figure_ids(self, query: str) -> List[str]:
        """Extract figure IDs from query"""
        figure_ids = []
        
        for pattern in self.figure_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                # Reconstruct full figure ID
                full_match = match.group(0)
                figure_ids.append(full_match)
        
        return list(set(figure_ids))  # Remove duplicates
    
    def _extract_table_ids(self, query: str) -> List[str]:
        """Extract table IDs from query"""
        table_ids = []
        
        for pattern in self.table_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                # Reconstruct full table ID
                full_match = match.group(0)
                table_ids.append(full_match)
        
        return list(set(table_ids))  # Remove duplicates
    
    def should_use_metadata_filtering(self, routing_result: Dict[str, Any]) -> bool:
        """Determine if metadata filtering should be applied"""
        return routing_result.get("should_filter", False)
    
    def get_filter_description(self, routing_result: Dict[str, Any]) -> str:
        """Get human-readable description of applied filters"""
        return routing_result.get("routing_strategy", "No special routing")
