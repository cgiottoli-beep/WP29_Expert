import streamlit as st
from supabase_client import SupabaseClient
from config import Config
import time

def debug_check():
    print("--- DEBUG START: OWNERSHIP CHECK ---")
    client = SupabaseClient.get_client()

    # Define symbols to check
    # 86 (Lightning/Hidden), 85 (Visible)
    symbols = ["ECE/TRANS/WP.29/2025/86", "ECE/TRANS/WP.29/2025/85"]
    
    for sym in symbols:
        print(f"\nChecking: {sym}")
        docs = client.table("documents").select("*").eq("symbol", sym).execute()
        if docs.data:
            d = docs.data[0]
            print(f"ID: {d.get('id')}")
            # Check for any owner/created_by fields. 
            # Note: Standard Supabase fields might not be in 'select *' if they are not columns, 
            # but usually 'user_id' or similar is used.
            print(f"Keys available: {list(d.keys())}")
            print(f"Created By/User ID: {d.get('user_id')} | {d.get('created_by')} | {d.get('owner')}")
            
            # Also check embeddings for this doc
            emb = client.table("embeddings").select("id, source_id, created_by", count="exact").eq("source_id", d['id']).limit(1).execute()
            print(f"Embeddings Count (Anon): {emb.count}")
            if emb.data:
                 print(f"Embedding Sample Keys: {list(emb.data[0].keys())}")
        else:
            print("Doc not found")

if __name__ == "__main__":
    debug_check()
