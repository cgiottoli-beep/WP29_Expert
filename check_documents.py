"""Check if documents were saved"""
from supabase_client import SupabaseClient

# Get GRE sessions
sessions = SupabaseClient.get_sessions_by_group('GRE')
print(f"Sessioni GRE trovate: {len(sessions)}")

if sessions:
    # Get documents for first session
    session = sessions[0]
    print(f"\nVerifica sessione: {session['code']} ({session['year']})")
    print(f"Session ID: {session['id']}")
    
    documents = SupabaseClient.get_documents_by_session(session['id'])
    print(f"\nDocumenti salvati: {len(documents)}")
    
    if documents:
        print("\nPrimi 5 documenti:")
        for i, doc in enumerate(documents[:5], 1):
            print(f"  {i}. {doc['symbol']}: {doc['title'][:60]}")
    else:
        print("\n[!] NESSUN DOCUMENTO TROVATO - Il salvataggio non ha funzionato")
else:
    print("[!] Nessuna sessione GRE trovata")
