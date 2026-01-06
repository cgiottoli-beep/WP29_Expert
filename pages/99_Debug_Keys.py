import streamlit as st
import os
import google.generativeai as genai
from config import Config
from auth_utils import require_auth

st.set_page_config(page_title="Debug Keys", page_icon="🐞")

require_auth()

st.title("🐞 API Key Debugger")

st.markdown("### 1. Environment Variables Check")

supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

st.write(f"**SUPABASE_URL Found:** {'✅' if supa_url else '❌'}")
if supa_url:
    st.code(f"{supa_url[:15]}...")

st.write(f"**SUPABASE_KEY Found:** {'✅' if supa_key else '❌'}")
if supa_key:
    st.code(f"{supa_key[:5]}...{supa_key[-5:] if len(supa_key)>10 else ''}")

st.write(f"**GOOGLE_API_KEY Found:** {'✅' if google_key else '❌'}")
if google_key:
    st.code(f"prefix: {google_key[:5]}... (Length: {len(google_key)})")
    
    if google_key.startswith("AIza"):
        st.success("Format looks correct (starts with AIza)")
    else:
        st.error("Format looks WRONG (Should start with 'AIza')")

st.markdown("---")
st.markdown("### 2. Connection Test")

if st.button("Test Google Gemini Connection"):
    try:
        genai.configure(api_key=google_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content("Hello, simply say 'OK'")
        st.success(f"Connection Successful! Response: {response.text}")
    except Exception as e:
        st.error(f"Connection Failed: {str(e)}")
        st.info("If this fails with 'API_KEY_INVALID', check Google Cloud Console for IP Restrictions.")

