"""Test file access and URL generation"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

print("=" * 70)
print("TESTING FILE ACCESS")
print("=" * 70)

# Get a document with file URL
docs = client.table("documents").select("*").limit(1).execute()

if docs.data and docs.data[0].get('file_url'):
    doc = docs.data[0]
    file_url = doc['file_url']
    
    print(f"\nDocument: {doc['symbol']}")
    print(f"Stored URL: {file_url}")
    
    # Extract file path
    file_path = file_url.split('/unece-archive/')[-1]
    print(f"File path: {file_path}")
    
    # Test different URL methods
    print(f"\n1. Testing get_public_url()...")
    try:
        public_url = client.storage.from_(Config.STORAGE_BUCKET).get_public_url(file_path)
        print(f"   Public URL: {public_url}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n2. Testing create_signed_url()...")
    try:
        signed_url_response = client.storage.from_(Config.STORAGE_BUCKET).create_signed_url(file_path, 3600)
        print(f"   Signed URL: {signed_url_response}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n3. Testing direct download...")
    try:
        file_data = client.storage.from_(Config.STORAGE_BUCKET).download(file_path)
        print(f"   Downloaded {len(file_data)} bytes successfully")
    except Exception as e:
        print(f"   Error: {e}")
        
else:
    print("No documents with file_url found")
