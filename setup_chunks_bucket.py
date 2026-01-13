"""
Setup script: Ensure chunks_cache bucket exists in Supabase Storage

Run this before using the new RAG architecture or running the migration.
"""

from supabase_client import SupabaseClient
from config import Config

def create_chunks_cache_bucket():
    """
    Create the chunks_cache bucket if it doesn't exist
    """
    client = SupabaseClient.get_client()
    
    print("=" * 60)
    print("CHUNKS_CACHE BUCKET SETUP")
    print("=" * 60)
    
    bucket_name = Config.CHUNKS_CACHE_BUCKET
    
    print(f"\nChecking if bucket '{bucket_name}' exists...")
    
    try:
        # Try to list buckets
        buckets = client.storage.list_buckets()
        bucket_names = [b['name'] for b in buckets]
        
        if bucket_name in bucket_names:
            print(f"✓ Bucket '{bucket_name}' already exists")
            return True
        
        # Create bucket if it doesn't exist
        print(f"Creating bucket '{bucket_name}'...")
        client.storage.create_bucket(
            bucket_name,
            options={
                "public": False,  # Private bucket (requires authentication)
                "file_size_limit": 1024 * 1024,  # 1MB per file (JSON chunks are small)
                "allowed_mime_types": ["application/json"]
            }
        )
        
        print(f"✓ Bucket '{bucket_name}' created successfully")
        
        # Set up RLS policies (if needed)
        print("\nNote: You may need to configure RLS policies in Supabase Dashboard:")
        print(f"  1. Go to Storage > {bucket_name}")
        print("  2. Set policies to allow authenticated users to read/write")
        
        return True
        
    except Exception as e:
        print(f"✗ Error setting up bucket: {e}")
        print("\nPlease create the bucket manually in Supabase Dashboard:")
        print(f"  1. Go to Storage")
        print(f"  2. Create new bucket: '{bucket_name}'")
        print("  3. Set as Private (not public)")
        print("  4. Configure RLS policies for authenticated access")
        return False


if __name__ == "__main__":
    print("\nThis script will create the chunks_cache bucket in Supabase Storage.\n")
    
    success = create_chunks_cache_bucket()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Setup complete! You can now:")
        print("  1. Run the database migration: alter_embeddings_for_storage.sql")
        print("  2. Run the data migration: migrate_chunks_to_storage.py")
        print("  3. Start ingesting new documents (they'll use Storage)")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  Setup incomplete. Please create bucket manually.")
        print("=" * 60)
