"""Check storage files and database consistency"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

# Get documents from database
print("=" * 70)
print("DATABASE DOCUMENTS")
print("=" * 70)

docs = client.table("documents").select("*").limit(5).execute()
print(f"\nTotal documents in DB: {len(docs.data)}")

if docs.data:
    print("\nFirst 5 documents:")
    for i, doc in enumerate(docs.data[:5], 1):
        print(f"\n{i}. {doc['symbol']}")
        print(f"   Title: {doc['title'][:60]}")
        print(f"   File URL: {doc.get('file_url', 'NO URL')}")

# Try to list files in storage
print("\n" + "=" * 70)
print("STORAGE FILES")
print("=" * 70)

try:
    # List files in bucket
    files = client.storage.from_(Config.STORAGE_BUCKET).list()
    print(f"\nTotal folders in root: {len(files)}")
    
    if files:
        print("\nRoot level folders:")
        for f in files[:10]:
            print(f"  - {f['name']} (type: {f.get('id', 'folder')})")
            
        # Try to list inside GRE folder
        print("\nListing GRE folder:")
        gre_files = client.storage.from_(Config.STORAGE_BUCKET).list('GRE')
        print(f"  Found {len(gre_files)} items")
        for f in gre_files[:5]:
            print(f"    - {f['name']}")
            
            if f['name'] not in ['.emptyFolderPlaceholder']:
                # Try to list year folders
                year_files = client.storage.from_(Config.STORAGE_BUCKET).list(f'GRE/{f["name"]}')
                print(f"      Items in {f['name']}: {len(year_files)}")
                for yf in year_files[:3]:
                    print(f"        - {yf['name']}")
    else:
        print("\n[!] NO FILES FOUND IN STORAGE!")
        
except Exception as e:
    print(f"\n[ERROR] Cannot list storage: {e}")

# Check if specific file exists
print("\n" + "=" * 70)
print("FILE EXISTENCE CHECK")
print("=" * 70)

if docs.data and docs.data[0].get('file_url'):
    test_url = docs.data[0]['file_url']
    print(f"\nTesting URL: {test_url}")
    
    # Extract path
    try:
        file_path = test_url.split('/unece-archive/')[-1]
        print(f"Extracted path: {file_path}")
        
        # Try to download
        result = client.storage.from_(Config.STORAGE_BUCKET).download(file_path)
        print(f"[OK] File exists! Size: {len(result)} bytes")
    except Exception as e:
        print(f"[ERROR] Cannot access file: {e}")
