"""
Quick setup and test script
"""
import subprocess
import sys

def run_command(cmd, description):
    """Run a shell command and report status"""
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Success!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"[FAIL] Failed!")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("UNECE WP.29 Archive - Setup Script")
    print("="*60)
    
    # Step 1: Install dependencies
    print("\nInstalling dependencies...")
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python packages"
    ):
        print("\nSome packages may have failed to install.")
        print("Please check the errors above.")
    
    # Step 2: Check configuration
    print("\nChecking configuration...")
    try:
        from config import Config
        print("[OK] Configuration loaded successfully")
        print(f"   - Supabase URL: {Config.SUPABASE_URL[:30]}...")
        print(f"   - Google API Key: {Config.GOOGLE_API_KEY[:20]}...")
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        print("\nPlease ensure .env file is properly configured")
        return
    
    # Step 3: Database setup instructions
    print("\n" + "="*60)
    print("DATABASE SETUP REQUIRED")
    print("="*60)
    print("""
Please complete the following steps in your Supabase dashboard:

1. Go to: https://pmocdqcnjcfxpqgmywiw.supabase.co
2. Navigate to: SQL Editor
3. Execute the SQL from: init_database.sql
4. Execute the SQL from: vector_search_function.sql

This will:
[OK] Enable pgvector extension
[OK] Create all required tables
[OK] Set up vector search functionality
""")
    
    # Step 4: Ready to run
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("""
To start the application, run:

    streamlit run Home.py

Then navigate to the URL shown in your terminal (usually http://localhost:8501)
""")

if __name__ == "__main__":
    main()
