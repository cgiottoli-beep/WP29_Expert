"""Test storage bucket access"""
from supabase_client import SupabaseClient
from config import Config

def test_bucket_access():
    """Test se il bucket è accessibile"""
    try:
        client = SupabaseClient.get_client()
        
        # Prova a creare un file di test
        test_content = b"Test file"
        test_path = "test/test.txt"
        
        print(f"Test upload su bucket '{Config.STORAGE_BUCKET}'...")
        
        # Upload test file
        result = client.storage.from_(Config.STORAGE_BUCKET).upload(
            test_path,
            test_content
        )
        
        print(f"[OK] Upload riuscito!")
        print(f"  Path: {test_path}")
        
        # Cleanup - rimuovi il file di test
        client.storage.from_(Config.STORAGE_BUCKET).remove([test_path])
        print(f"[OK] File di test rimosso")
        
        print(f"\n[SUCCESS] Bucket '{Config.STORAGE_BUCKET}' e' configurato correttamente!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Test fallito: {error_msg}")
        
        if "not found" in error_msg.lower():
            print("\nIl bucket non esiste o il nome non e' corretto.")
            print(f"Nome atteso: '{Config.STORAGE_BUCKET}'")
        elif "policy" in error_msg.lower():
            print("\nProblema di permessi RLS (Row Level Security).")
            print("Potrebbe essere necessario configurare le policy del bucket.")
        
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Test Accesso Storage Bucket")
    print("=" * 60)
    print()
    
    test_bucket_access()
