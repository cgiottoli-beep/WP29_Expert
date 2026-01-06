
from supabase_client import SupabaseClient
import json

def check_content():
    print("Fetching one embedding row...")
    try:
        response = SupabaseClient.get_client().table("embeddings").select("*").limit(1).execute()
        if not response.data:
            print("Table is empty (unexpected, since count was 1082?)")
            return
            
        row = response.data[0]
        print("Row keys:", row.keys())
        
        # Check embedding field
        emb = row.get('embedding')
        if emb is None:
            print("WARNING: 'embedding' field is None!")
        else:
            # It might be a string or list depending on client
            if isinstance(emb, str):
                print(f"Embedding is string of length {len(emb)}")
                # Try to parse if it looks like json?
                try: 
                    emb_list = json.loads(emb)
                    print(f"Parsed vector length: {len(emb_list)}")
                except:
                    print("Could not parse string.")
            elif isinstance(emb, list):
                print(f"Embedding is list of length {len(emb)}")
            else:
                print(f"Embedding is type {type(emb)}")

    except Exception as e:
        print(f"Error fetching row: {e}")

if __name__ == "__main__":
    check_content()
