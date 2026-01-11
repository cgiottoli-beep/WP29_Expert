from supabase_client import SupabaseClient

try:
    groups = SupabaseClient.get_all_groups()
    print("\n--- GROUP HIERARCHY ---")
    for g in groups:
        parent = g['parent_group_id'] if g['parent_group_id'] else "ROOT"
        print(f"ID: {g['id']} | Type: {g['type']} | Parent: {parent}")

except Exception as e:
    print(f"Error: {e}")
