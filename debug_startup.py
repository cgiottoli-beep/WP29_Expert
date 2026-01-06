import sys
print("1. Starting debug script...", flush=True)

try:
    print("2. Importing streamlit...", flush=True)
    import streamlit as st
    print("   -> Success", flush=True)
except Exception as e:
    print(f"   -> Failed: {e}", flush=True)

try:
    print("3. Importing supabase_client...", flush=True)
    from supabase_client import SupabaseClient
    print("   -> Success", flush=True)
except Exception as e:
    print(f"   -> Failed: {e}", flush=True)

try:
    print("4. Importing embedding_service...", flush=True)
    from embedding_service import EmbeddingService
    print("   -> Success", flush=True)
except Exception as e:
    print(f"   -> Failed: {e}", flush=True)

print("5. All imports finished. Setup complete.", flush=True)
