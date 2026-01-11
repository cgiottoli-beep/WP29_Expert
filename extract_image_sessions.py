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
    Analyze this image which contains a list of sessions for a Working Group (TF GP).
    Extract the following information for each session in JSON format:
    - code: The session number (e.g., "1", "2", "3", "0"). If it says "1st session", code is "1". If "kick-off", code might be "0".
    - year: The year of the session (e.g., 2025).
    - dates: The date string (e.g., "2025-01-23").
    
    Ignore "Literature materials" or "Terms of Reference". Only extract items that look like sessions/meetings.

    Return a JSON list of objects:
    [
        {"code": "0", "year": 2025, "dates": "2025-01-23"},
        ...
    ]
    RETURN ONLY JSON.
    """
    
    print("Asking Gemini to analyze image...")
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
    # 1. Find group ID for TF GP
    groups = SupabaseClient.get_all_groups()
    tfgp_id = None
    for g in groups:
        if g['id'] == 'TF GP' or 'Glare Prevention' in g['full_name']:
            tfgp_id = g['id']
            break
            
    if not tfgp_id:
        # Fallback query if not found in cache/list
        print("TF GP not found in get_all_groups, checking DB directly...")
        client = SupabaseClient.get_client()
        res = client.table('groups').select('id').eq('id', 'TF GP').execute()
        if res.data:
            tfgp_id = res.data[0]['id']
        else:
            print("TF GP group not found! Please create it first.")
            return

    print(f"Target Group ID: {tfgp_id}")

    # 2. Extract from Image
    # Path provided by user metadata/context
    image_path = "C:/Users/cgiot/.gemini/antigravity/brain/b2c9b8a2-584e-4ee3-aae0-1b400a648a61/uploaded_image_1768169183130.png"
    
    sessions = extract_sessions_from_image(image_path)
    
    if not sessions:
        print("No sessions extracted.")
        return

    # 3. Insert Sessions
    print("Inserting sessions...")
    for s in sessions:
        try:
            print(f"Creating session {s['code']} ({s['year']})...")
            # SupabaseClient.create_session(group_id, code, year, dates)
            # Check if exists first maybe? Supabase usually errors on duplicate PK or allows upsert depending on policy.
            # We'll just try to create.
            SupabaseClient.create_session(
                group_id=tfgp_id,
                code=str(s['code']),
                year=int(s['year']),
                dates=s['dates']
            )
            print("Success.")
        except Exception as e:
            print(f"Error inserting session {s}: {e}")

if __name__ == "__main__":
    main()
