"""
Check actual content_path values in DB
"""
from supabase_client import SupabaseClient

client = SupabaseClient.get_client()

# Get sample embeddings with their actual content_path values
print("=== Checking actual content_path values ===\n")

# Sample from documents
docs = client.table("embeddings").select("id, source_type, content_path, content_chunk").eq("source_type", "document").limit(10).execute()

print("Sample 10 DOCUMENT embeddings:")
for i, e in enumerate(docs.data):
    path = e.get('content_path')
    chunk = e.get('content_chunk')
    print(f"{i+1}. Path: {path if path else 'NULL'}")
    print(f"   Chunk: {'Present (' + str(len(chunk)) + ' chars)' if chunk else 'NULL'}")
    print()

# Check the specific ones from search results
print("\n=== Checking search result sources ===")
result_ids = [
    "c773b6ef-366d-41f9-8e17-7940c4447ec7",  # interpretation
    "d0152dad-0dee-4806-9522-11c1b8446e07",  # document
    "b9aaf911-e495-41b0-8490-66caa8cce601"   # document
]

for source_id in result_ids:
    embs = client.table("embeddings").select("id, content_path, content_chunk").eq("source_id", source_id).limit(1).execute()
    if embs.data:
        e = embs.data[0]
        print(f"\nSource: {source_id[:20]}...")
        print(f"  content_path: {e.get('content_path') if e.get('content_path') else 'NULL'}")
        print(f"  content_chunk: {'Present' if e.get('content_chunk') else 'NULL'}")
