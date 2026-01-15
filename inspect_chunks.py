"""
Download and display all chunks from TFGP-04-03
"""
from supabase_client import SupabaseClient

# Get document ID
client = SupabaseClient.get_client()
docs = client.table("documents").select("id, symbol, title").eq("symbol", "TFGP-04-03").execute()

doc_id = docs.data[0]['id']
print(f"Document: {docs.data[0]['symbol']}")
print(f"Title: {docs.data[0]['title']}\n")

# Get chunks
for i in range(8):
    try:
        storage_path = f"{doc_id}/chunk_{i}.json"
        chunk_data = SupabaseClient.download_json(storage_path)
        text = chunk_data.get('text', '')
        
        print(f"=== CHUNK {i} ===")
        print(f"Length: {len(text)} chars")
        print(f"Preview: {text[:200]}")
        
        # Check for "glare" keyword
        glare_count = text.lower().count('glare')
        if glare_count > 0:
            print(f"*** Contains 'glare' {glare_count} times ***")
        print()
    except Exception as e:
        print(f"Error loading chunk {i}: {e}\n")
