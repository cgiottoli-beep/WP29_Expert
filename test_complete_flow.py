"""
Simulate complete search flow to find failure point
"""
from embedding_service import EmbeddingService

print("Testing complete search flow...")

query = "logo"
print(f"Query: {query}\n")

try:
    results = EmbeddingService.search_with_reranking(query, limit=5)
    
    print(f"Returned {len(results)} results\n")
    
    if not results:
        print("NO RESULTS - AI Assistant will show 'No relevant documents found'")
    else:
        for i, r in enumerate(results):
            print(f"=== Result {i+1} ===")
            print(f"  Source: {r.get('source_id')}")
            print(f"  Type: {r.get('source_type')}")
            print(f"  Similarity: {r.get('similarity')}")
            print(f"  Has content_chunk: {'content_chunk' in r and r['content_chunk'] is not None and len(r['content_chunk']) > 0}")
            
            if 'content_chunk' in r and r['content_chunk']:
                preview = r['content_chunk'][:100].replace('\n', ' ')
                print(f"  Preview: {preview}...")
            else:
                print(f"  *** NO CONTENT_CHUNK! ***")
                print(f"  content_path: {r.get('content_path')}")
            print()
            
except Exception as e:
    print(f"ERROR in search: {e}")
    import traceback
    traceback.print_exc()
