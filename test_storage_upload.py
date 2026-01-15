"""
Test script to verify if upload_json works
"""
from supabase_client import SupabaseClient
import json

print("Testing storage upload...")

# Test data
test_data = {
    "text": "This is a test chunk",
    "source_id": "test_doc_123",
    "source_type": "document",
    "chunk_index": 0,
    "authority_level": 1
}

storage_path = "test_doc_123/chunk_0.json"

try:
    print(f"Attempting to upload to: {storage_path}")
    result = SupabaseClient.upload_json(storage_path, test_data)
    print(f"✅ SUCCESS! Uploaded to: {result}")
except Exception as e:
    print(f"❌ FAILED!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    import traceback
    traceback.print_exc()
