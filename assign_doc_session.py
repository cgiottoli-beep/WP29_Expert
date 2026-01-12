from supabase_client import SupabaseClient

def main():
    doc_symbol = "ECE/TRANS/WP.29/1186"
    target_session_code = "196"
    target_group_id = "WP29" # Should match what we used before ("WP29" or "WP.29")
    target_year = 2025
    target_dates = "24-27 June 2025" # From search result
    
    client = SupabaseClient.get_client()
    
    # 1. Find the Group ID (Verify if WP29 or WP.29)
    # In extract_wp29_sessions.py we used "WP.29" as fallback if "WP29" missing.
    # Let's check which one has sessions.
    # Actually, let's just search for the group first.
    
    groups = SupabaseClient.get_all_groups()
    group_id = None
    for g in groups:
        if g['id'] in ['WP29', 'WP.29']:
            group_id = g['id']
            break
            
    if not group_id:
        print("Error: Could not find WP29 group.")
        return
        
    print(f"Using Group ID: {group_id}")
    
    # 2. Find or Create Session 196
    print(f"Checking for Session {target_session_code}...")
    sessions = SupabaseClient.get_sessions_by_group(group_id)
    session_id = None
    for s in sessions:
        if str(s['code']) == target_session_code:
            session_id = s['id']
            print(f"Found existing Session 196: {session_id}")
            break
            
    if not session_id:
        print("Session 196 not found. Creating it...")
        # create_session returns the created object or response? 
        # The static method currently doesn't return the ID, so we re-fetch.
        SupabaseClient.create_session(
            group_id=group_id,
            code=target_session_code,
            year=target_year,
            dates=target_dates
        )
        # Re-fetch to get ID
        sessions = SupabaseClient.get_sessions_by_group(group_id)
        for s in sessions:
            if str(s['code']) == target_session_code:
                session_id = s['id']
                break
        print(f"Created Session 196: {session_id}")

    if not session_id:
        print("Error: Failed to get Session ID.")
        return

    # 3. Find the Document
    print(f"Finding document {doc_symbol}...")
    
    try:
        # Search directly by symbol column
        res = client.table('documents').select('id, symbol').eq('symbol', doc_symbol).execute()
        if res.data:
            target_doc_id = res.data[0]['id']
            print(f"Found document ID: {target_doc_id}")
        else:
             print("Document not found by exact symbol match.")
             
    except Exception as e:
        print(f"Error searching documents: {e}")
        
    if not target_doc_id:
        return

    # 4. Update Document Session
    print(f"Updating document {target_doc_id} to Session {session_id}...")
    try:
        data = client.table('documents').update({'session_id': session_id}).eq('id', target_doc_id).execute()
        print("Update successful.")
    except Exception as e:
        print(f"Error updating document: {e}")

if __name__ == "__main__":
    main()
