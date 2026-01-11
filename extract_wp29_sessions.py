import os
import json
import google.generativeai as genai
from PIL import Image
from config import Config
from supabase_client import SupabaseClient

# Configure Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

def extract_sessions_from_image(image_path):
    print(f"Loading image from {image_path}...")
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return []

    print(f"Using model: {Config.GEMINI_FLASH_MODEL}")
    model = genai.GenerativeModel(Config.GEMINI_FLASH_MODEL)
    
    prompt = """
    Analyze this image which contains a list of WP.29 sessions in Italian.
    Example line: "1. Sessione 195 - 4-7 marzo 2025, Ginevra"
    
    Extract the following information for each session in JSON format:
    - code: The session number (e.g., "195", "194").
    - year: The year of the session (e.g., 2025). Extract from the date string.
    - dates: The full date string (e.g., "4-7 marzo 2025"). Translate month to English if you want, or keep original. Let's keep original Italian string for 'dates' field as it is display only.

    Return a JSON list of objects:
    [
        {"code": "195", "year": 2025, "dates": "4-7 marzo 2025"},
        ...
    ]
    RETURN ONLY JSON.
    """
    
    print("Asking Gemini to analyze image...")
    minutes_waited = 0
    # Simple retry loop or just one call
    response = model.generate_content([prompt, img])
    
    json_str = response.text.strip()
    # Cleanup markdown
    if json_str.startswith("```"):
        parts = json_str.split("```")
        if len(parts) >= 2:
            json_str = parts[1]
            if json_str.strip().startswith("json"):
                json_str = json_str.strip()[4:].strip()
    
    try:
        sessions = json.loads(json_str)
        print(f"Extracted {len(sessions)} sessions.")
        return sessions
    except Exception as e:
        print(f"Error parsing JSON: {e}\nRaw output: {json_str}")
        return []

def main():
    # 1. Target Group: WP29
    # Identify ID
    # Usually "WP29" or "WP.29". Let's check or assume "WP29" based on previous knowledge or lookup.
    # In Admin_Structure.py lines we saw "WP29" as root group.
    
    target_group_id = "WP29" 
    
    # Double check if it exists in DB to be safe
    client = SupabaseClient.get_client()
    res = client.table('groups').select('id').eq('id', target_group_id).execute()
    if not res.data:
        # Try WP.29
        target_group_id = "WP.29"
        res = client.table('groups').select('id').eq('id', target_group_id).execute()
        if not res.data:
             print("Could not find WP29 or WP.29 group.")
             return

    print(f"Target Group ID: {target_group_id}")

    # 2. Extract from Image
    image_path = "C:/Users/cgiot/.gemini/antigravity/brain/b2c9b8a2-584e-4ee3-aae0-1b400a648a61/uploaded_image_1768170392546.png"
    
    sessions = extract_sessions_from_image(image_path)
    
    if not sessions:
        print("No sessions extracted.")
        return

    # 3. Insert Sessions
    print("Inserting sessions...")
    for s in sessions:
        try:
            print(f"Creating session {s['code']} ({s['year']})...")
            SupabaseClient.create_session(
                group_id=target_group_id,
                code=str(s['code']),
                year=int(s['year']),
                dates=s['dates']
            )
            print("Success.")
        except Exception as e:
            print(f"Error inserting session {s}: {e}")

if __name__ == "__main__":
    main()
