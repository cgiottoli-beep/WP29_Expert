"""
Script di test per verificare lo stato della quota Gemini API
"""
import google.generativeai as genai
from config import Config
import time

genai.configure(api_key=Config.GOOGLE_API_KEY)

def test_api_quota():
    """Test semplice per verificare se la quota è disponibile"""
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content("Say 'OK' in one word")
        print("[OK] API FUNZIONANTE - Quota disponibile!")
        print(f"   Risposta: {response.text}")
        return True
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            print("[X] QUOTA SUPERATA - Aspetta ancora...")
            print(f"   Errore: {error_str[:100]}")
            return False
        else:
            print(f"[!] ALTRO ERRORE: {error_str[:150]}")
            return False

if __name__ == "__main__":
    print("Test quota Gemini API...")
    print("=" * 60)
    
    # Test ogni 30 secondi fino a quando funziona
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        print(f"\nTentativo {attempt}/{max_attempts}...")
        
        if test_api_quota():
            print("\n[OK] LA QUOTA E' STATA RESETTATA!")
            print("Ora puoi usare l'app normalmente.")
            break
        
        if attempt < max_attempts:
            print(f"[WAIT] Attendo 30 secondi prima del prossimo tentativo...")
            time.sleep(30)
    else:
        print("\n[!] Quota ancora non disponibile dopo tutti i tentativi.")
        print("Prova piu tardi o considera di usare una nuova API key.")
