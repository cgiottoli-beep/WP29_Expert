"""Test file deletion for recently uploaded files"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

print("=" * 70)
print("TESTING FILE DELETION")
print("=" * 70)

# Get recent documents
docs = client.table("documents").select("*").order("created_at", desc=True).limit(5).execute()

print(f"\nFound {len(docs.data)} recent documents:\n")

for doc in docs.data:
    file_url = doc.get('file_url')
    print(f"Symbol: {doc['symbol']}")
    print(f"  File URL: {file_url}")
    
    if file_url:
        # Test path extraction
        try:
            # Method 1: Using split with bucket name
            path1 = file_url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
            print(f"  Extracted path (method 1): {path1}")
            
            # Method 2: More robust
            if '/object/public/' in file_url:
                parts = file_url.split('/object/public/')[-1]
                path2 = parts.split('/', 1)[-1] if '/' in parts else parts
                print(f"  Extracted path (method 2): {path2}")
            
            # Test if file exists in storage
            try:
                file_list = client.storage.from_(Config.STORAGE_BUCKET).list(path1.rsplit('/', 1)[0])
                filename = path1.rsplit('/', 1)[-1]
                file_exists = any(f['name'] == filename for f in file_list)
                print(f"  File exists in storage: {file_exists}")
            except Exception as e:
                print(f"  Error checking file: {e}")
                
        except Exception as e:
            print(f"  Error extracting path: {e}")
    else:
        print(f"  No file URL")
    
    print()
