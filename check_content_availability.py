"""
Check how many embeddings have NO content at all
"""
from supabase_client import SupabaseClient

client = SupabaseClient.get_client()

# Count embeddings by content availability
total = client.table("embeddings").select("id", count="exact").execute().count
with_chunk = client.table("embeddings").select("id", count="exact").not_.is_("content_chunk", "null").execute().count
with_path = client.table("embeddings").select("id", count="exact").not_.is_("content_path", "null").execute().count

print(f"Total embeddings: {total}")
print(f"With content_chunk (old): {with_chunk}")
print(f"With content_path (new): {with_path}")

neither = total - max(with_chunk, with_path)  # Rough estimate
print(f"\nPotentially missing content: {neither}")

# Sample some results to see structure
print("\n=== Sample 5 random embeddings ===")
sample = client.table("embeddings").select("id, source_type, content_chunk, content_path").limit(5).execute()

for i, emb in enumerate(sample.data):
    has_chunk = emb.get('content_chunk') is not None
    has_path = emb.get('content_path') is not None
    print(f"\n{i+1}. ID: {emb['id'][:8]}...")
    print(f"   Type: {emb['source_type']}")
    print(f"   Has content_chunk: {has_chunk}")
    print(f"   Has content_path: {has_path}")
    if not has_chunk and not has_path:
        print("   *** NO CONTENT AT ALL! ***")
