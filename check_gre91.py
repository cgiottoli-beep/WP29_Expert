"""
Script to check if specific GRE-91 documents exist and have embeddings
"""
from supabase_client import SupabaseClient

def check_documents():
    client = SupabaseClient.get_client()
    
    # Documents the user expects to find
    search_terms = ["GRE-91", "GRE-2024-13", "GRE-2024-11", "GRE/91"]
    
    print("=" * 60)
    print("CHECKING FOR GRE-91 / GRE-2024 DOCUMENTS")
    print("=" * 60)
    
    for term in search_terms:
        print(f"\n[SEARCH] Searching for symbol containing: '{term}'")
        
        # Search in documents table
        docs = client.table("documents").select("id, symbol, title").ilike("symbol", f"%{term}%").execute()
        
        if docs.data:
            for doc in docs.data:
                print(f"  [OK] Found: {doc['symbol']}")
                print(f"     Title: {doc['title'][:60]}...")
                
                # Check embeddings
                emb = client.table("embeddings").select("id", count="exact").eq("source_id", doc['id']).execute()
                print(f"     Embeddings: {emb.count}")
        else:
            print(f"  [X] No documents found")
    
    # Also check total documents in GRE sessions from 2024
    print("\n" + "=" * 60)
    print("CHECKING GRE SESSION 91 DOCUMENTS")
    print("=" * 60)
    
    # Find session 91 for GRE
    sessions = client.table("sessions").select("id, code, year, group_id").eq("code", "91").execute()
    
    for session in sessions.data:
        print(f"\nSession: {session['group_id']} - {session['code']} ({session['year']})")
        
        docs = client.table("documents").select("id, symbol, title").eq("session_id", session['id']).execute()
        print(f"Documents in this session: {len(docs.data)}")
        
        for doc in docs.data[:5]:  # Show first 5
            emb = client.table("embeddings").select("id", count="exact").eq("source_id", doc['id']).execute()
            status = "[OK]" if emb.count > 0 else "[!]"
            print(f"  {status} {doc['symbol']} - Chunks: {emb.count}")
        
        if len(docs.data) > 5:
            print(f"  ... and {len(docs.data) - 5} more")

if __name__ == "__main__":
    check_documents()
