"""
Migration Script: Move existing chunk content from DB to Storage

This script:
1. Selects all embeddings with content_chunk but no content_path
2. Uploads chunk text to Storage as JSON
3. Updates DB record with content_path
4. Optionally sets content_chunk to NULL to free space
5. Runs VACUUM FULL to reclaim disk space

Run this script once to migrate existing data to the new architecture.
"""

from supabase_client import SupabaseClient
from config import Config
import time

def migrate_chunks_to_storage(batch_size: int = 100, set_null: bool = False):
    """
    Migrate existing chunks from DB to Storage
    
    Args:
        batch_size: Number of records to process at once
        set_null: If True, set content_chunk to NULL after migration
    """
    client = SupabaseClient.get_client()
    
    print("=" * 60)
    print("CHUNK MIGRATION TO STORAGE")
    print("=" * 60)
    
    # Step 1: Count total records to migrate
    print("\n[1/5] Counting chunks to migrate...")
    count_response = client.table("embeddings") \
        .select("id", count="exact") \
        .not_.is_("content_chunk", "null") \
        .is_("content_path", "null") \
        .execute()
    
    total_count = count_response.count
    print(f"    Found {total_count} chunks to migrate")
    
    if total_count == 0:
        print("\n✓ No chunks to migrate. All done!")
        return
    
    # Step 2: Migrate in batches
    print(f"\n[2/5] Migrating chunks in batches of {batch_size}...")
    migrated_count = 0
    error_count = 0
    
    while migrated_count < total_count:
        # Fetch a batch
        batch_response = client.table("embeddings") \
            .select("id, source_id, source_type, content_chunk, authority_level") \
            .not_.is_("content_chunk", "null") \
            .is_("content_path", "null") \
            .limit(batch_size) \
            .execute()
        
        batch = batch_response.data
        
        if not batch:
            break  # No more records
        
        for idx, record in enumerate(batch):
            try:
                # Create JSON payload
                chunk_data = {
                    "text": record['content_chunk'],
                    "source_id": record['source_id'],
                    "source_type": record['source_type'],
                    "authority_level": record['authority_level']
                }
                
                # Generate storage path
                # Use the embedding ID to ensure uniqueness
                storage_path = f"{record['source_id']}/chunk_{record['id']}.json"
                
                # Upload to Storage
                SupabaseClient.upload_json(storage_path, chunk_data)
                
                # Update DB with path
                update_data = {"content_path": storage_path}
                if set_null:
                    update_data["content_chunk"] = None
                
                client.table("embeddings") \
                    .update(update_data) \
                    .eq("id", record['id']) \
                    .execute()
                
                migrated_count += 1
                
                # Progress indicator
                if migrated_count % 10 == 0:
                    print(f"    Progress: {migrated_count}/{total_count} ({migrated_count*100//total_count}%)")
                
            except Exception as e:
                error_count += 1
                print(f"    ERROR migrating chunk {record['id']}: {e}")
        
        # Small delay between batches to avoid rate limiting
        time.sleep(0.5)
    
    print(f"\n    Migrated: {migrated_count}")
    print(f"    Errors: {error_count}")
    
    # Step 3: Verify migration
    print("\n[3/5] Verifying migration...")
    verify_response = client.table("embeddings") \
        .select("id", count="exact") \
        .not_.is_("content_chunk", "null") \
        .is_("content_path", "null") \
        .execute()
    
    remaining = verify_response.count
    print(f"    Remaining unmigrated chunks: {remaining}")
    
    if remaining > 0:
        print(f"\n⚠️  WARNING: {remaining} chunks still need migration. Re-run script or check errors.")
        return
    
    # Step 4: Set content_chunk to NULL if not already done
    if not set_null:
        print("\n[4/5] Setting content_chunk to NULL to free space...")
        print("    (This will take a moment...)")
        
        try:
            # Update all records that have content_path but still have content_chunk
            null_response = client.table("embeddings") \
                .update({"content_chunk": None}) \
                .not_.is_("content_path", "null") \
                .not_.is_("content_chunk", "null") \
                .execute()
            
            print(f"    ✓ Cleared content_chunk for migrated records")
        except Exception as e:
            print(f"    ERROR clearing content_chunk: {e}")
    
    # Step 5: VACUUM FULL (This must be run manually via SQL editor)
    print("\n[5/5] Database cleanup...")
    print("\n" + "=" * 60)
    print("IMPORTANT: FINAL STEP REQUIRED")
    print("=" * 60)
    print("\nTo reclaim disk space, you must run this SQL command")
    print("in your Supabase SQL Editor:\n")
    print("    VACUUM FULL embeddings;\n")
    print("This will compact the table and release space to the OS.")
    print("Without this step, the database size will not decrease.")
    print("=" * 60)
    
    print("\n✓ Migration complete!")
    print(f"  Total migrated: {migrated_count}")
    print(f"  Total errors: {error_count}")


if __name__ == "__main__":
    import sys
    
    print("\nThis script will migrate chunk text from Database to Storage.")
    print("It is safe to run multiple times (already migrated chunks are skipped).\n")
    
    # Ask for confirmation
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("Migration cancelled.")
        sys.exit(0)
    
    # Run migration
    migrate_chunks_to_storage(batch_size=100, set_null=True)
