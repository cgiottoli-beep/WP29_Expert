"""Test file deletion from Supabase Storage"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

# Get one document
docs = client.table("documents").select("*").limit(1).execute()

if docs.data:
    doc = docs.data[0]
    print(f"Testing deletion for: {doc['symbol']}")
    print(f"File URL: {doc.get('file_url', 'NO URL')}")
    
    if doc.get('file_url'):
        # Extract file path
        file_path = doc['file_url'].split('/unece-archive/')[-1]
        print(f"Extracted path: {file_path}")
        
        # Try to delete
        try:
            result = client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
            print(f"[OK] Deletion result: {result}")
        except Exception as e:
            print(f"[ERROR] Deletion failed: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("[!] Document has no file URL")
else:
    print("[!] No documents in database")
