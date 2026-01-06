
import time
from gemini_client import GeminiClient
from supabase_client import SupabaseClient

def debug_search():
    query = "What are the latest changes to R48?"
    print(f"DEBUG SCENARIO: Search for '{query}'")
    
    # 1. Generate Embedding
    print("\n[1] Generating query embedding via Gemini...")
    start = time.time()
    try:
        query_embedding = GeminiClient.generate_query_embedding(query)
        print(f"    Success! generated vector of length {len(query_embedding)}")
        print(f"    Time taken: {time.time() - start:.2f}s")
        
        # Check if vector is all zeros (error case in GeminiClient)
        if all(x == 0 for x in query_embedding):
            print("    WARNING: Vector is all zeros! Embedding generation failed internally.")
    except Exception as e:
        print(f"    ERROR generating embedding: {e}")
        return

    # 2. Vector Search
    print("\n[2] Searching Supabase embeddings...")
    start = time.time()
    try:
        results = SupabaseClient.search_embeddings(query_embedding, limit=20)
        print(f"    Success! Returned {len(results)} results")
        print(f"    Time taken: {time.time() - start:.2f}s")
        
        if results:
            print("    Top result:")
            top = results[0]
            print(f"      ID: {top.get('id')}")
            print(f"      Similarity: {top.get('similarity')}")
            print(f"      Content preview: {top.get('content_chunk')[:50]}...")
    except Exception as e:
        print(f"    ERROR during vector search: {e}")
        return

    # 3. Re-ranking logic simulation
    print("\n[3] Re-ranking (local)...")
    try:
        ranked_results = sorted(
            results,
            key=lambda x: (x.get('authority_level', 0), x.get('similarity', 0)),
            reverse=True
        )
        print("    Re-ranking complete.")
        if ranked_results:
             print(f"    Top ranked: {ranked_results[0].get('similarity')} (Authority: {ranked_results[0].get('authority_level')})")
    except Exception as e:
         print(f"    ERROR during re-ranking: {e}")

if __name__ == "__main__":
    debug_search()
