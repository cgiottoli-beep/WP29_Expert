"""Test PDF upload with correct MIME type"""
from supabase_client import SupabaseClient
from config import Config
import os

# Test with an existing file
client = SupabaseClient.get_client()

# Get first document to test re-upload
docs = client.table("documents").select("*").limit(1).execute()

if docs.data:
    doc = docs.data[0]
    print(f"Testing with document: {doc['symbol']}")
    print(f"Current file URL: {doc.get('file_url')}")
    
    # Try to download the existing file
    if doc.get('file_url'):
        try:
            file_path = doc['file_url'].split('/unece-archive/')[-1]
            print(f"\nDownloading: {file_path}")
            file_bytes = client.storage.from_(Config.STORAGE_BUCKET).download(file_path)
            print(f"Downloaded {len(file_bytes)} bytes")
            
            # Re-upload with correct MIME type
            print(f"\nRe-uploading with correct MIME type...")
            new_url = SupabaseClient.upload_file(file_path, file_bytes)
            print(f"New URL: {new_url}")
            
            # Check metadata
            print(f"\nChecking file metadata...")
            files = client.storage.from_(Config.STORAGE_BUCKET).list(os.path.dirname(file_path))
            for f in files:
                if f['name'] == os.path.basename(file_path):
                    print(f"File metadata: {f}")
                    if 'metadata' in f:
                        print(f"  MIME type: {f['metadata'].get('mimetype')}")
            
            print("\n✅ Test complete!")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
else:
    print("No documents found to test")
