"""
Test vector search for glare query
"""
from embedding_service import EmbeddingService

print("Testing search_with_reranking...")

query = "cosa trovi su glare prevention?"

try:
    results = EmbeddingService.search_with_reranking(query, limit=5)
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source ID: {result.get('source_id')}")
        print(f"Source Type: {result.get('source_type')}")
        print(f"Similarity: {result.get('similarity')}")
        print(f"Content path: {result.get('content_path')}")
        print(f"Content chunk present: {'content_chunk' in result and result['content_chunk'] is not None}")
        if 'content_chunk' in result and result['content_chunk']:
            print(f"Content preview: {result['content_chunk'][:100]}...")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
