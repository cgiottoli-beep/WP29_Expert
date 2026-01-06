"""Check what's currently in storage"""
from supabase_client import SupabaseClient
from config import Config

client = SupabaseClient.get_client()

print("=" * 70)
print("CURRENT STORAGE CONTENTS")
print("=" * 70)

try:
    # List files in GRE/2025/93
    files = client.storage.from_(Config.STORAGE_BUCKET).list('GRE/2025/93')
    
    print(f"\nFiles in GRE/2025/93: {len(files)}\n")
    for file in files:
        print(f"  - {file['name']}")
        print(f"    Size: {file['metadata'].get('size', 'unknown')} bytes")
        print(f"    Type: {file['metadata'].get('mimetype', 'unknown')}")
        print()
        
except Exception as e:
    print(f"Error: {e}")

# Check database
print("\n" + "=" * 70)
print("DATABASE DOCUMENTS")
print("=" * 70)

docs = client.table("documents").select("*").execute()
print(f"\nTotal documents in database: {len(docs.data)}\n")
