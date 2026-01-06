"""Cleanup orphaned files from storage"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

print("=" * 70)
print("CLEANUP ORPHANED FILES")
print("=" * 70)

# These files exist in storage but NOT in database
orphaned_files = [
    "GRE/2025/93/GRE-93-28 Rev1.pdf",
    "GRE/2025/93/GRE-93-29 Rev1 e.pdf"
]

print(f"\nFound {len(orphaned_files)} orphaned files to delete:\n")
for file_path in orphaned_files:
    print(f"  - {file_path}")

proceed = input("\nDo you want to delete these files? (yes/no): ")

if proceed.lower() == 'yes':
    deleted_count = 0
    failed_count = 0
    
    for file_path in orphaned_files:
        try:
            client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
            print(f"  [OK] Deleted: {file_path}")
            deleted_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to delete {file_path}: {e}")
            failed_count += 1
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Deleted: {deleted_count}")
    print(f"Failed: {failed_count}")
else:
    print("\nCancelled. No files were deleted.")
