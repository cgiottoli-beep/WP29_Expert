"""Check current bucket configuration"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

print("=" * 70)
print("CHECKING BUCKET CONFIGURATION")
print("=" * 70)

try:
    # List all buckets
    buckets = client.storage.list_buckets()
    
    print(f"\nAvailable buckets:")
    for bucket in buckets:
        print(f"  - {bucket.name} (public: {bucket.public})")
        if bucket.name == Config.STORAGE_BUCKET:
            print(f"    >> This is our active bucket")
            print(f"    >> Public: {bucket.public}")
            print(f"    >> ID: {bucket.id}")
    
    # Check if our bucket exists
    our_bucket = next((b for b in buckets if b.name == Config.STORAGE_BUCKET), None)
    
    if our_bucket:
        print(f"\n[FOUND] Bucket '{Config.STORAGE_BUCKET}'")
        print(f"  Public: {our_bucket.public}")
        
        if not our_bucket.public:
            print(f"\n⚠️  PROBLEM: Bucket is PRIVATE but we're using get_public_url()")
            print(f"  Solution: Make bucket public or use signed URLs")
    else:
        print(f"\n[NOT FOUND] Bucket '{Config.STORAGE_BUCKET}' doesn't exist!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
