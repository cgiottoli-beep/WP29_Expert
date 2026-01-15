"""
Test download_json functionality
"""
from supabase_client import SupabaseClient

print("Testing download_json...")

# Try to download the first chunk from TFGP-04-03
# The doc_id should be in the database
try:
    # First, get the document ID for TFGP-04-03
    client = SupabaseClient.get_client()
    docs = client.table("documents").select("id").eq("symbol", "TFGP-04-03").execute()
    
    if not docs.data:
        print("ERROR: TFGP-04-03 not found!")
    else:
        doc_id = docs.data[0]['id']
        print(f"Found document ID: {doc_id}")
        
        # Try to download chunk_0.json
        storage_path = f"{doc_id}/chunk_0.json"
        print(f"Attempting to download: {storage_path}")
        
        chunk_data = SupabaseClient.download_json(storage_path)
        print(f"SUCCESS! Downloaded chunk:")
        print(f"  Text preview: {chunk_data.get('text', '')[:100]}...")
        print(f"  Source: {chunk_data.get('source_id')}")
        print(f"  Chunk index: {chunk_data.get('chunk_index')}")
        
except Exception as e:
    print(f"FAILED!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
