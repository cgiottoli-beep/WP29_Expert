
from supabase_client import SupabaseClient

def check_count():
    print("Checking 'embeddings' table count...")
    try:
        # Supabase-py doesn't have a direct count method on table() easily without select
        # But we can use select(count='exact', head=True)
        response = SupabaseClient.get_client().table("embeddings").select("*", count="exact", head=True).execute()
        print(f"Total embeddings: {response.count}")
        
    except Exception as e:
        print(f"Error checking count: {e}")

if __name__ == "__main__":
    check_count()
