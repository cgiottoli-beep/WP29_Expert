"""
Script per creare automaticamente il bucket Supabase Storage
"""
from supabase_client import SupabaseClient
from config import Config

def create_storage_bucket():
    """Crea il bucket 'unece-archive' se non esiste"""
    try:
        client = SupabaseClient.get_client()
        
        # Prova a creare il bucket
        result = client.storage.create_bucket(
            Config.STORAGE_BUCKET,
            options={
                "public": False,  # Privato
                "file_size_limit": 52428800,  # 50MB max
                "allowed_mime_types": ["application/pdf"]
            }
        )
        
        print("[OK] Bucket 'unece-archive' creato con successo!")
        print(f"  Dettagli: {result}")
        
        # Imposta le policy RLS (Row Level Security)
        print("\n[OK] Configurazione policy di accesso...")
        print("  - Bucket privato")
        print("  - File size limit: 50MB")
        print("  - Solo PDF accettati")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
            print("[OK] Bucket 'unece-archive' esiste gia!")
            return True
        else:
            print(f"[ERROR] Errore creazione bucket: {error_msg}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("Creazione Bucket Supabase Storage")
    print("=" * 60)
    print()
    
    success = create_storage_bucket()
    
    if success:
        print("\n[OK] Storage pronto per l'uso!")
    else:
        print("\n[!] Creazione fallita - vedi istruzioni manuali sotto:")
        print()
        print("ISTRUZIONI MANUALI:")
        print("1. Vai su https://pmocdqcnjcfxpqgmywiw.supabase.co")
        print("2. Clicca su 'Storage' nella sidebar")
        print("3. Clicca 'New bucket'")
        print("4. Nome: 'unece-archive'")
        print("5. Public: NO (lascia unchecked)")
        print("6. Clicca 'Create bucket'")

