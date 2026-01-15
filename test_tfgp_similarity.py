"""
Check embeddings for new TFGP-04-03 document
"""
from supabase_client import SupabaseClient
from gemini_client import GeminiClient

# Get document ID
client = SupabaseClient.get_client()
docs = client.table("documents").select("id, symbol").eq("symbol", "TFGP-04-03").execute()

if not docs.data:
    print("TFGP-04-03 not found!")
else:
    doc_id = docs.data[0]['id']
    print(f"Document ID: {doc_id}\n")
    
    # Get embeddings for this document
    embs = client.table("embeddings").select("id, content_path").eq("source_id", doc_id).execute()
    print(f"Found {len(embs.data)} embeddings for TFGP-04-03")
    
    if embs.data:
        print(f"All have content_path: {all(e.get('content_path') for e in embs.data)}")
        
        # Now test similarity with query
        query = "glare prevention"
        print(f"\nGenerating embedding for query: '{query}'")
        query_emb = GeminiClient.generate_embedding(query)
        
        # Search with this embedding
        print("\nSearching...")
        results = SupabaseClient.search_embeddings(query_emb, limit=20)
        
        # Check if our document appears
        our_doc_positions = [i for i, r in enumerate(results) if r.get('source_id') == doc_id]
        
        if our_doc_positions:
            print(f"\nFOUND! TFGP-04-03 at positions: {our_doc_positions}")
            for pos in our_doc_positions[:3]:
                result = results[pos]
                print(f"  Position {pos}: similarity = {result.get('similarity')}")
        else:
            print(f"\nNOT FOUND! TFGP-04-03 NOT in top 20 results!")
            print("\nTop 5 results:")
            for i, r in enumerate(results[:5]):
                print(f"  {i+1}. similarity={r.get('similarity'):.4f}, source_id={r.get('source_id')}")
