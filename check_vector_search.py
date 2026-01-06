
from supabase_client import SupabaseClient
import time

def check_rpc():
    print("Checking 'match_embeddings' RPC function...")
    try:
        # Create a dummy zero vector of dimension 768
        dummy_vector = [0.0] * 768
        
        print("Calling RPC...")
        start_time = time.time()
        
        # We need to access the client directly or use search_embeddings
        # Using search_embeddings wrapper
        results = SupabaseClient.search_embeddings(dummy_vector, limit=1)
        
        end_time = time.time()
        print(f"RPC call successful! Took {end_time - start_time:.2f} seconds.")
        print(f"Returned {len(results)} results.")
        if results:
            print("Sample result Keys:", results[0].keys())
            
    except Exception as e:
        print(f"RPC call FAILED: {e}")
        print("\nPossible causes:")
        print("1. Function 'match_embeddings' does not exist in Supabase (did you run vector_search_function.sql?)")
        print("2. pgvector extension is not enabled")
        print("3. Arguments mismatch (dimension 768 vs database?)")

if __name__ == "__main__":
    check_rpc()
