"""Check for orphaned files in storage"""
from supabase_client import SupabaseClient

client = SupabaseClient.get_client()

print("=" * 70)
print("CHECKING FOR ORPHANED FILES")
print("=" * 70)

# Get all documents from database
all_docs = client.table("documents").select("*").execute()

# Get file URLs from database
db_file_urls = [doc.get('file_url') for doc in all_docs.data if doc.get('file_url')]

print(f"\nTotal documents in DB: {len(all_docs.data)}")
print(f"Documents with files: {len(db_file_urls)}")

# Extract file paths
db_file_paths = []
for url in db_file_urls:
    try:
        # URL format: https://.../storage/v1/object/public/unece-archive/path/to/file.pdf
        path = url.split('/unece-archive/')[-1]
        db_file_paths.append(path)
    except:
        pass

# List all files in storage
try:
    storage_files = client.storage.from_('unece-archive').list()
    
    print(f"\n Checking storage folders...")
    
    # Check GRE folder
    gre_files = client.storage.from_('unece-archive').list('GRE/2025/93')
    
    print(f"\nFiles in GRE/2025/93: {len(gre_files)}")
    for file in gre_files:
        file_path = f"GRE/2025/93/{file['name']}"
        in_db = file_path in db_file_paths
        status = "In DB" if in_db else "ORPHANED"
        print(f"  [{status}] {file['name']}")
        
except Exception as e:
    print(f"Error listing storage: {e}")

# Check specifically for the problematic files
print("\n" + "=" * 70)
print("CHECKING SPECIFIC FILES")
print("=" * 70)

problem_files = ["GRE-93-28 Ravr.pdf", "GRE-93-29 Ravr1.e.pdf"]

for filename in problem_files:
    # Check if exists in database
    matching_docs = [doc for doc in all_docs.data 
                     if doc.get('file_url') and filename in doc['file_url']]
    
    print(f"\nFile: {filename}")
    print(f"  In database: {len(matching_docs)} records")
    
    if matching_docs:
        for doc in matching_docs:
            print(f"    - Symbol: {doc['symbol']}")
            print(f"    - URL: {doc['file_url']}")
            print(f"    - ID: {doc['id']}")
