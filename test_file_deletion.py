"""Debug file deletion - test with actual file"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

# Get a document with file_url
docs = client.table("documents").select("*").limit(1).execute()

if docs.data and docs.data[0].get('file_url'):
    doc = docs.data[0]
    file_url = doc['file_url']
    
    print("=" * 70)
    print("FILE DELETION TEST")
    print("=" * 70)
    print(f"\nDocument: {doc['symbol']}")
    print(f"File URL: {file_url}")
    
    # Extract path
    file_path = file_url.split('/unece-archive/')[-1]
    print(f"Extracted path: {file_path}")
    
    # Test 1: Check if file exists
    print("\n[1] Checking if file exists...")
    try:
        download_result = client.storage.from_(Config.STORAGE_BUCKET).download(file_path)
        print(f"    [OK] File exists, size: {len(download_result)} bytes")
    except Exception as e:
        print(f"    [ERROR] File not found: {e}")
        exit(1)
    
    # Test 2: Try to delete
    print("\n[2] Attempting to delete file...")
    try:
        remove_result = client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
        print(f"    Result: {remove_result}")
        print(f"    Result type: {type(remove_result)}")
        
        # Check the response structure
        if hasattr(remove_result, 'data'):
            print(f"    Result.data: {remove_result.data}")
        if hasattr(remove_result, 'error'):
            print(f"    Result.error: {remove_result.error}")
            
    except Exception as e:
        print(f"    [ERROR] Deletion failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check if file still exists
    print("\n[3] Checking if file was actually deleted...")
    try:
        download_result = client.storage.from_(Config.STORAGE_BUCKET).download(file_path)
        print(f"    [FAIL] File still exists! Size: {len(download_result)} bytes")
        print("    >> Deletion did NOT work!")
    except Exception as e:
        print(f"    [OK] File not found (successfully deleted)")
        print("    >> Deletion worked!")
    
else:
    print("[!] No documents with file_url found in database")
