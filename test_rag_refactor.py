"""
Test script for RAG refactoring: Storage-based chunks

Tests:
1. Bucket exists and is accessible
2. Upload/Download JSON to/from chunks_cache
3. Create embedding with content_path (new architecture)
4. Retrieve and populate chunk content from Storage
"""

from supabase_client import SupabaseClient
from embedding_service import EmbeddingService
from gemini_client import GeminiClient
from config import Config
import uuid

def test_storage_operations():
    """Test basic Storage operations"""
    print("\n[TEST 1] Storage Operations")
    print("-" * 40)
    
    try:
        # Test upload
        test_data = {
            "text": "This is a test chunk for the new storage architecture.",
            "source_id": "test-doc-123",
            "source_type": "document",
            "chunk_index": 0,
            "authority_level": 1
        }
        
        test_path = "test/chunk_0.json"
        
        print(f"  Uploading test JSON to: {test_path}")
        SupabaseClient.upload_json(test_path, test_data)
        print("  ✓ Upload successful")
        
        # Test download
        print(f"  Downloading test JSON from: {test_path}")
        downloaded_data = SupabaseClient.download_json(test_path)
        print("  ✓ Download successful")
        
        # Verify content
        assert downloaded_data['text'] == test_data['text'], "Text mismatch"
        assert downloaded_data['source_id'] == test_data['source_id'], "Source ID mismatch"
        print("  ✓ Content verified")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_embedding_with_storage():
    """Test creating embedding with content_path"""
    print("\n[TEST 2] Embedding with Storage Path")
    print("-" * 40)
    
    try:
        # Generate a test embedding
        test_text = "Electric vehicles must comply with Regulation R100."
        embedding = GeminiClient.generate_embedding(test_text)
        
        print("  ✓ Generated test embedding")
        
        # Upload chunk to Storage
        test_id = str(uuid.uuid4())
        chunk_data = {
            "text": test_text,
            "source_id": test_id,
            "source_type": "document",
            "chunk_index": 0,
            "authority_level": 1
        }
        
        storage_path = f"{test_id}/chunk_0.json"
        SupabaseClient.upload_json(storage_path, chunk_data)
        print(f"  ✓ Uploaded chunk to: {storage_path}")
        
        # Create embedding record with content_path
        result = SupabaseClient.create_embedding(
            source_id=test_id,
            source_type="document",
            embedding=embedding,
            authority_level=1,
            content_path=storage_path
        )
        
        print(f"  ✓ Created embedding record: {result['id']}")
        
        # Verify it was stored correctly
        assert result['content_path'] == storage_path, "Path mismatch"
        assert result['content_chunk'] is None, "content_chunk should be NULL"
        print("  ✓ Embedding stored with path (no content in DB)")
        
        # Clean up
        client = SupabaseClient.get_client()
        client.table("embeddings").delete().eq("id", result['id']).execute()
        print("  ✓ Cleaned up test data")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_retrieval_with_storage():
    """Test retrieving chunks from Storage"""
    print("\n[TEST 3] Retrieval with Parallel Fetching")
    print("-" * 40)
    
    try:
        # Create a mock result set (simulating DB query results)
        test_id = str(uuid.uuid4())
        storage_path = f"{test_id}/chunk_0.json"
        
        # Upload test chunk
        chunk_data = {
            "text": "Test chunk content for retrieval",
            "source_id": test_id,
            "source_type": "document",
            "chunk_index": 0,
            "authority_level": 1
        }
        SupabaseClient.upload_json(storage_path, chunk_data)
        print(f"  ✓ Uploaded test chunk to: {storage_path}")
        
        # Simulate search results
        mock_results = [
            {
                "id": str(uuid.uuid4()),
                "content_path": storage_path,
                "content_chunk": None,  # Simulating new architecture
                "similarity": 0.85,
                "authority_level": 1
            }
        ]
        
        # Test population
        print("  Fetching chunk content from Storage...")
        populated_results = EmbeddingService._populate_chunk_content(mock_results)
        
        # Verify
        assert len(populated_results) == 1, "Results count mismatch"
        assert populated_results[0]['content_chunk'] == chunk_data['text'], "Content mismatch"
        print("  ✓ Content successfully fetched from Storage")
        print(f"     Retrieved text: '{populated_results[0]['content_chunk']}'")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("RAG REFACTORING TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Storage Operations", test_storage_operations),
        ("Embedding with Storage", test_embedding_with_storage),
        ("Retrieval with Storage", test_retrieval_with_storage)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✓ All tests passed! RAG refactoring is working correctly.")
    else:
        print("\n✗ Some tests failed. Please review errors above.")
    
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
