from supabase_client import SupabaseClient

def main():
    group_id = 'TF GP'
    
    print(f"Creating 'Literature materials' session for {group_id}...")
    
    try:
        # We use Year 2025 as a default placeholder
        SupabaseClient.create_session(
            group_id=group_id,
            code="Literature",
            year=2025,
            dates="General Materials"
        )
        print("Success: Created 'Literature' session.")
    except Exception as e:
        print(f"Error creating session: {e}")
        
    try:
        # Also create 'Terms of Reference' if missing, as it was in the image too?
        # The user only asked for "Literature materials" specifically.
        # But let's check if we should do Terms of Reference independently.
        # User prompt: "perche non hai create Literature materials" -> singular.
        # I will stick to just Literature for now.
        pass
    except Exception as e:
        pass

if __name__ == "__main__":
    main()
