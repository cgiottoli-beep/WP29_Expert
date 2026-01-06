"""Debug organization structure data"""
from supabase_client import SupabaseClient

groups = SupabaseClient.get_all_groups()

print("=" * 70)
print("GROUP HIERARCHY DEBUG")
print("=" * 70)

print(f"Total groups found: {len(groups)}")

for g in groups:
    pid = g.get('parent_group_id')
    print(f"Group: {g['id']}")
    print(f"  Parent: {pid}")
    print(f"  Description: {g.get('description')}")
    print("-" * 30)

# Check top level logic
top_level = [g['id'] for g in groups if not g.get('parent_group_id')]
print(f"\nIdentified Top Level (No Parent): {top_level}")
