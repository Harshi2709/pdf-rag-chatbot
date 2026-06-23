from vectordb.chroma_client import ChromaDBClient

def debug_chroma():
    print("\n" + "="*60)
    print("CHROMADB: Checking stored table chunks")
    print("="*60)
    
    client = ChromaDBClient(persist_directory="./chroma_db")
    print(f"Total chunks in DB: {client.get_collection_count()}")
    
    # Get everything and filter for tables
    results = client.collection.get(include=["documents", "metadatas"])
    
    table_chunks = [
        (doc, meta) for doc, meta in 
        zip(results["documents"], results["metadatas"])
        if meta.get("chunk_type") == "table" or "TABLE" in doc
    ]
    
    print(f"Table chunks found: {len(table_chunks)}")
    for doc, meta in table_chunks:
        print(f"\n  ID      : {meta.get('table_id', 'unknown')}")
        print(f"  Size    : {len(doc)} chars")
        print(f"  Caption : {meta.get('caption', 'none')}")
        print(f"  Preview :\n{doc[:400]}")

debug_chroma()