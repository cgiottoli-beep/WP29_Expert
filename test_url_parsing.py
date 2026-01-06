"""Test URL parsing from actual Supabase uploads"""
from supabase_client import SupabaseClient
from config import Config

# Simulate a file upload and get the URL
print("=" * 70)
print("TEST URL FORMAT FROM UPLOAD")
print("=" * 70)

# Create a tiny test file
test_content = b"test"
test_path = "GRE/2025/93/test-deletion.txt"

client = SupabaseClient.get_client()

try:
    # Upload test file
    response = client.storage.from_(Config.STORAGE_BUCKET).upload(
        test_path,
        test_content,
        file_options={"upsert": "true"}
    )
    print(f"\nUpload response: {response}")
    
    # Get URL
    url = client.storage.from_(Config.STORAGE_BUCKET).get_public_url(test_path)
    print(f"\nGenerated URL:\n{url}")
    
    #Test extraction methods
    print(f"\n{'='*70}")
    print("EXTRACTION METHODS")
    print(f"{'='*70}\n")
    
    # Method 1: Current code
    try:
        path1 = url.split('/unece-archive/')[-1]
        print(f"Method 1 (current): {path1}")
    except Exception as e:
        print(f"Method 1 FAILED: {e}")
    
    # Method 2: Alternative
    try:
        path2 = url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
        print(f"Method 2 (with bucket var): {path2}")
    except Exception as e:
        print(f"Method 2 FAILED: {e}")
    
    # Method 3: Most robust
    try:
        if '/object/public/' in url:
            after_public = url.split('/object/public/')[-1]
            path3 = '/'.join(after_public.split('/')[1:])  # Skip bucket name
            print(f"Method 3 (robust): {path3}")
    except Exception as e:
        print(f"Method 3 FAILED: {e}")
    
    # Now test deletion
    print(f"\n{'='*70}")
    print("TESTING DELETION")
    print(f"{'='*70}\n")
    
    # Try deleting with extracted path
    delete_path = url.split(f'/{Config.STORAGE_BUCKET}/')[-1]
    print(f"Attempting to delete: {delete_path}")
    
    result = client.storage.from_(Config.STORAGE_BUCKET).remove([delete_path])
    print(f"Delete result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
