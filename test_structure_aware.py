"""
Test Script for Structure-Aware RAG
Tests figure queries, table queries, and metadata routing
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def _query_sample(question: str, debug: bool = True) -> Dict[str, Any]:
    """Send a query to the chat API"""
    print(f"📝 Query: {question}")
    
    payload = {
        "question": question,
        "debug": debug
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✅ Answer: {result['answer'][:200]}...")
        
        # Show metadata info
        if 'metadata' in result:
            print(f"\n📊 Metadata:")
            print(f"  - Chunks retrieved: {result['metadata'].get('num_chunks_retrieved')}")
            print(f"  - Query type: {result['metadata'].get('query_type', 'N/A')}")
        
        # Show debug info
        if debug and 'debug_info' in result:
            debug_info = result['debug_info']
            
            if 'query_routing' in debug_info:
                routing = debug_info['query_routing']
                print(f"\n🔍 Query Routing:")
                print(f"  - Type: {routing.get('query_type')}")
                print(f"  - Strategy: {routing.get('routing_strategy')}")
                print(f"  - Detected entities: {routing.get('detected_entities', [])}")
            
            if 'chunk_types_retrieved' in debug_info:
                chunk_types = debug_info['chunk_types_retrieved']
                print(f"\n📦 Chunk Types Retrieved:")
                from collections import Counter
                type_counts = Counter(chunk_types)
                for chunk_type, count in type_counts.items():
                    print(f"  - {chunk_type}: {count}")
        
        # Show citations
        if 'citations' in result and result['citations']:
            print(f"\n📚 Citations:")
            for citation in result['citations'][:3]:
                cit_str = f"  - {citation['file']}, Page {citation['page']}"
                if 'type' in citation:
                    cit_str += f" [{citation['type']}]"
                if 'figure_id' in citation:
                    cit_str += f" ({citation['figure_id']})"
                if 'table_id' in citation:
                    cit_str += f" ({citation['table_id']})"
                print(cit_str)
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        return {}


def _status_sample():
    """Test the status endpoint"""
    print_section("System Status")
    
    try:
        response = requests.get(f"{BASE_URL}/status")
        response.raise_for_status()
        status = response.json()
        
        print(f"✅ Backend Status:")
        print(f"  - Vector DB count: {status.get('vector_db_count', 0)} chunks")
        print(f"  - Pipeline type: {status.get('pipeline_type', 'standard')}")
        print(f"  - Ollama available: {status.get('ollama_available', False)}")
        print(f"  - Model: {status.get('model', 'N/A')}")
        
        if 'documents' in status:
            print(f"\n📄 Uploaded Documents:")
            for doc in status['documents']:
                print(f"  - {doc['filename']} ({doc['chunk_count']} chunks)")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print_section("Structure-Aware RAG Test Suite")
    
    # Test 1: Check system status
    if not _status_sample():
        print("\n❌ Backend is not running or not accessible")
        print("Please start the backend with: python backend/main.py")
        return
    
    # Test 2: Figure queries
    print_section("Test 1: Figure Queries")
    
    _query_sample("What is shown in Figure 4?")
    print("\n" + "-"*60 + "\n")
    _query_sample("Explain the architecture in Figure 2")
    print("\n" + "-"*60 + "\n")
    _query_sample("Describe Figure 1")
    
    # Test 3: Table queries
    print_section("Test 2: Table Queries")
    
    _query_sample("What does Table I contain?")
    print("\n" + "-"*60 + "\n")
    _query_sample("What are the values in Table II?")
    print("\n" + "-"*60 + "\n")
    _query_sample("Which model performed best according to Table I?")
    
    # Test 4: General queries (should still work)
    print_section("Test 3: General Queries")
    
    _query_sample("What is the main contribution of the paper?")
    print("\n" + "-"*60 + "\n")
    _query_sample("Explain the methodology")
    
    # Test 5: Mixed queries
    print_section("Test 4: Mixed Queries")
    
    _query_sample("Compare the architecture in Figure 2 with the results in Table I")
    
    print_section("Tests Complete")
    
    print("""
✅ Test suite finished!

If you see:
- Query Type: "figure" or "table" → Structure-aware routing is working
- Chunk Types: "figure", "table" → Structured chunks are being retrieved
- Citations with [figure] or [table] → Metadata is preserved

If queries fail:
1. Make sure you re-uploaded documents after the upgrade
2. Check that USE_STRUCTURE_AWARE_RAG=true in .env
3. Verify Docling is installed: pip install docling

For more info, see: PHASE2_STRUCTURE_AWARE_UPGRADE.md
""")


if __name__ == "__main__":
    main()
