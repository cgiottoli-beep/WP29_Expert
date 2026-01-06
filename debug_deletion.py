"""Debug deletion issue - check what happens when trying to delete"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

print("=" * 70)
print("TESTING DELETION SCENARIO")
print("=" * 70)

# Get all documents
docs = client.table("documents").select("*").execute()

print(f"\nDocuments in database: {len(docs.data)}\n")

if docs.data:
    for doc in docs.data:
        print(f"Symbol: {doc['symbol']}")
        print(f"  ID: {doc['id']}")
        print(f"  File URL: {doc.get('file_url', 'NO FILE URL')}")
        
        if doc.get('file_url'):
            # Test path extraction
            file_url = doc['file_url']
            try:
                file_path = file_url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
                print(f"  Extracted path: {file_path}")
                
                # Try to delete
                print(f"  Attempting deletion...")
                result = client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
                print(f"  Delete result: {result}")
                
                # Delete from database
                client.table("documents").delete().eq("id", doc['id']).execute()
                print(f"  Database record deleted: YES")
                
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  No file URL - skipping storage deletion")
        
        print()
        
        # Only test first document
        break
else:
    print("No documents to test!")
    
    # Check storage directly
    print("\nChecking storage contents...")
    try:
        files = client.storage.from_(Config.STORAGE_BUCKET).list('GRE/2025/93')
        print(f"Files in storage: {len(files)}")
        for f in files:
            print(f"  - {f['name']}")
    except Exception as e:
        print(f"Error: {e}")
