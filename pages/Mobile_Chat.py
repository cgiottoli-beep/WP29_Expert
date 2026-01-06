"""
Mobile-Optimized AI Assistant
Simplified interface for smartphone usage.
"""
import streamlit as st
from embedding_service import EmbeddingService
from gemini_client import GeminiClient
from supabase_client import SupabaseClient
from auth_utils import require_auth

# Mobile Configuration: Collapsed sidebar, wide layout
st.set_page_config(page_title="Mobile Assistant", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# Auth Check
require_auth()

# --- MOBILE CSS STYLING ---
st.markdown("""
<style>
    /* Mobile font optimization */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide top header decoration to save space */
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    
    /* Add padding for top status bar area */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important; /* Space for fixed bottom input */
    }
    
    /* User Message Style */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #e3f2fd;
        border-radius: 15px 15px 2px 15px;
        padding: 10px;
        border: 1px solid #bbdefb;
    }
    
    /* Assistant Message Style */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #f5f5f5;
        border-radius: 15px 15px 15px 2px;
        padding: 10px;
        border: 1px solid #e0e0e0;
    }
    
    /* Input area optimization */
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 10px 15px;
        font-size: 16px; /* Prevent iOS zoom on focus */
    }
    
    /* Button optimization */
    div.stButton > button {
        border-radius: 20px;
        height: 45px;
        font-weight: bold;
    }
    
    /* Sources Expander styling */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.subheader("📱 WP.29 Assistant")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Display chat history (Simplified for Mobile)
for message in st.session_state.chat_history:
    role = message['role']
    with st.chat_message(role):
        st.markdown(message['content'])

# Input Area
user_query = st.chat_input("Message WP.29 AI...")

if user_query:
    # Add to history
    st.session_state.chat_history.append({'role': 'user', 'content': user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # 1. Search
                relevant_chunks = EmbeddingService.search_with_reranking(user_query, limit=5) # Reduced limit for mobile
                
                # 2. Enrich Citations
                enriched_chunks = []
                if relevant_chunks:
                    for chunk in relevant_chunks:
                        # Get document info (Simplified retrieval)
                        # ... (Reusing logic but keeping it compact)
                        file_url = None
                        if chunk['source_type'] == 'document':
                            doc = SupabaseClient.get_client().table("documents").select("symbol, title, file_url").eq("id", chunk['source_id']).execute()
                            if doc.data:
                                chunk['symbol'] = doc.data[0]['symbol']
                                file_url = doc.data[0].get('file_url')
                        elif chunk['source_type'] == 'interpretation':
                            interp = SupabaseClient.get_client().table("interpretations").select("title, file_url").eq("id", chunk['source_id']).execute()
                            if interp.data:
                                chunk['symbol'] = "Interpretation"
                                file_url = interp.data[0].get('file_url')
                        else:
                            reg = SupabaseClient.get_client().table("regulation_versions").select("regulation_id, series, file_url").eq("id", chunk['source_id']).execute()
                            if reg.data:
                                chunk['symbol'] = f"Reg {reg.data[0]['regulation_id']}"
                                file_url = reg.data[0].get('file_url')
                        
                        if file_url:
                            chunk['signed_url'] = SupabaseClient.get_signed_url(file_url)
                        enriched_chunks.append(chunk)

                    # 3. Generate Answer
                    response = GeminiClient.chat_with_context(user_query, enriched_chunks)
                else:
                    response = "No relevant documents found."
                
                # Display Answer
                st.markdown(response)
                
                # Sources (Collapsed by default, simplified)
                if enriched_chunks:
                    with st.expander("📚 View Sources", expanded=False):
                        for chunk in enriched_chunks:
                            symbol = chunk.get('symbol', 'Doc')
                            url = chunk.get('signed_url')
                            if url:
                                st.markdown(f"🔗 [{symbol}]({url})")
                            else:
                                st.markdown(f"📄 {symbol}")
                
                # Save to history
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Hidden sidebar hack to allow navigation back
with st.sidebar:
    st.markdown("### Mobile Options")
    if st.button("🔄 Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
    st.page_link("Home.py", label="🏠 Home / Desktop Mode")
