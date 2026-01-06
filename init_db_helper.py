"""
Database initialization helper script
Run this to set up your Supabase database from Python
"""
from supabase import create_client
from config import Config
import os

def init_database():
    """Initialize Supabase database with schema and vector search function"""
    
    print("Connecting to Supabase...")
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # Read SQL files
    sql_files = [
        'init_database.sql',
        'vector_search_function.sql'
    ]
    
    for sql_file in sql_files:
        if not os.path.exists(sql_file):
            print(f"⚠️ Warning: {sql_file} not found, skipping...")
            continue
        
        print(f"\nReading {sql_file}...")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"ℹ️ SQL file loaded ({len(sql_content)} characters)")
        print("\n" + "="*70)
        print(f"Please execute the following SQL in your Supabase SQL Editor:")
        print("="*70)
        print(sql_content)
        print("="*70)
    
    print("\n✅ SQL files are ready!")
    print("\nManual steps:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the SQL content shown above")
    print("4. Run the queries")
    print("\nNote: The Supabase Python client doesn't support direct DDL execution,")
    print("so you need to run the SQL manually in the Supabase dashboard.")

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your .env file is properly configured with:")
        print("- SUPABASE_URL")
        print("- SUPABASE_KEY")
        print("- GOOGLE_API_KEY")
