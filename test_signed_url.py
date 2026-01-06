"""Test signed URL generation"""
from supabase_client import SupabaseClient

# Get a document with file URL
client = SupabaseClient.get_client()
docs = client.table("documents").select("*").limit(1).execute()

if docs.data and docs.data[0].get('file_url'):
    doc = docs.data[0]
    public_url = doc['file_url']
    
    print("=" * 70)
    print("TESTING SIGNED URL GENERATION")
    print("=" * 70)
    print(f"\nDocument: {doc['symbol']}")
    print(f"\nPublic URL:")
    print(f"  {public_url}")
    
    print(f"\nGenerating signed URL (24h expiration)...")
    signed_url = SupabaseClient.get_signed_url(public_url)
    
    print(f"\nSigned URL:")
    print(f"  {signed_url}")
    
    print(f"\nURL type: {'Signed' if '/sign/' in signed_url else 'Public'}")
    print(f"Has token: {'Yes' if 'token=' in signed_url else 'No'}")
    
    print(f"\n✅ Test complete!")
else:
    print("No documents found")
