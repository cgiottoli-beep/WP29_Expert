"""
Page 5: AI Assistant
RAG-powered chatbot for document search
"""
import streamlit as st
from embedding_service import EmbeddingService
from gemini_client import GeminiClient
from supabase_client import SupabaseClient

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("🤖 AI Assistant")
st.markdown("Ask questions about regulations and working documents")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ============================================================================
# CHAT INTERFACE
# ============================================================================

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Initialize input state if not present
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# Chat input area
with st.container():
    with st.form(key='search_form', clear_on_submit=True):
        col1, col2 = st.columns([10, 1])
        with col1:
            user_input = st.text_area("Ask a question:", value=st.session_state.input_text, height=100, label_visibility="collapsed", placeholder="Ask a question about UNECE regulations...")
        with col2:
            st.write("") # Spacer
            st.write("")
            submit_button = st.form_submit_button("⏩", use_container_width=True)
            
    if submit_button and user_input:
        user_query = user_input
        # Clear the pre-fill state after submission so it doesn't stick
        st.session_state.input_text = ""
    else:
        user_query = None

if user_query:
    # Add user message to history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_query
    })
    
    # Display user message
    with st.chat_message('user'):
        st.markdown(user_query)
    
    # Generate response
    with st.chat_message('assistant'):
        with st.spinner("Searching documents..."):
            try:
                # Search for relevant chunks with re-ranking (Increased limit for mixed results)
                relevant_chunks = EmbeddingService.search_with_reranking(user_query, limit=15)
                
                # Debug: Show optimized query to user
                from gemini_client import GeminiClient
                optimized_q = GeminiClient.optimize_query(user_query)
                st.caption(f"🔍 *Search keywords: {optimized_q[:100]}{'...' if len(optimized_q) > 100 else ''}*")
                
                if not relevant_chunks:
                    response = "I couldn't find any relevant documents to answer your question. Please try rephrasing or check if documents have been uploaded."
                else:
                    # Fetch full document info for citations
                    enriched_chunks = []
                    for chunk in relevant_chunks:
                        # Get document info
                        file_url = None
                        if chunk['source_type'] == 'document':
                            doc = SupabaseClient.get_client().table("documents").select("symbol, title, file_url").eq("id", chunk['source_id']).execute()
                            if doc.data:
                                chunk['symbol'] = doc.data[0]['symbol']
                                chunk['doc_title'] = doc.data[0]['title']
                                file_url = doc.data[0].get('file_url')
                        elif chunk['source_type'] == 'interpretation':
                            interp = SupabaseClient.get_client().table("interpretations").select("title, file_url, issue_date").eq("id", chunk['source_id']).execute()
                            if interp.data:
                                date = interp.data[0].get('issue_date', 'Unknown Date')
                                chunk['symbol'] = f"Interpretation ({date})"
                                chunk['doc_title'] = interp.data[0]['title']
                                file_url = interp.data[0].get('file_url')
                        else:
                            # Regulation
                            reg = SupabaseClient.get_client().table("regulation_versions").select("regulation_id, series, revision, file_url").eq("id", chunk['source_id']).execute()
                            if reg.data:
                                chunk['symbol'] = f"{reg.data[0]['regulation_id']} {reg.data[0]['series']}"
                                chunk['doc_title'] = f"Regulation {reg.data[0]['regulation_id']}"
                                file_url = reg.data[0].get('file_url')
                        
                        # Generate signed URL if file exists
                        if file_url:
                            chunk['signed_url'] = SupabaseClient.get_signed_url(file_url)
                        
                        enriched_chunks.append(chunk)
                    
                    # Generate answer using Gemini
                    response = GeminiClient.chat_with_context(user_query, enriched_chunks)
                
                # Display response
                st.markdown(response)
                
                # Show sources
                if relevant_chunks:
                    with st.expander("📚 Sources"):
                        seen_symbols = set()
                        for chunk in enriched_chunks:
                            # Use symbol as unique identifier
                            symbol_text = chunk.get('symbol', 'Unknown')
                            
                            # Skip duplicates
                            if symbol_text in seen_symbols:
                                continue
                            seen_symbols.add(symbol_text)
                            
                            # Calculate match percentage
                            score = float(chunk.get('similarity', 0)) * 100
                            match_badge = f"`Matched {score:.0f}%`"
                            
                            if chunk.get('signed_url'):
                                st.markdown(f"**[{symbol_text}]({chunk['signed_url']})** | {match_badge}")
                            else:
                                st.markdown(f"**{symbol_text}** | {match_badge}")
                                
                            st.markdown(f"*{chunk.get('doc_title', 'Unknown Title')}*")
                            
                            # Clean up content chunk for preview
                            clean_chunk = chunk['content_chunk'][:300].replace('\n', ' ').replace('#', '').strip()
                            st.caption(f"_{clean_chunk}..._")
                            st.markdown("---")
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}\n\nPlease ensure:\n1. Documents have been uploaded\n2. Embeddings have been generated\n3. Database vector search is properly configured"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg
                })

# Sidebar with info and controls
with st.sidebar:
    st.markdown("### 💡 How to Use")
    st.markdown("""
    This AI assistant uses **Retrieval Augmented Generation (RAG)** to answer questions based on:
    - Official regulations
    - Session reports
    - Working documents
    
    **Example questions:**
    - What are the latest changes to R48?
    - Summarize GRE Session 90 discussions on DRL
    - What did Italy propose regarding headlamps?
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    st.info("RAG uses authority-based ranking:\n- 🔟 Reports & Regulations\n- 1️⃣ Proposals")
    
    with st.expander("🛠️ Debug Info"):
        try:
            client = SupabaseClient.get_client()
            total_count = client.table("embeddings").select("id", count="exact").execute().count
            interp_count = client.table("embeddings").select("id", count="exact").eq("source_type", "interpretation").execute().count
            st.write(f"Total Embeddings: {total_count}")
            st.write(f"Interpretations: {interp_count}")
            
            if st.button("Test Search (Cosine > 0)"):
                # Test query without filters
                q = GeminiClient.generate_query_embedding("ESC")
                res = client.rpc("match_embeddings", {
                    "query_embedding": q,
                    "match_count": 5,
                    "filter_min_similarity": 0.0 # Force retrieve
                }).execute()
                st.write(f"Matches found: {len(res.data)}")
                if res.data:
                    st.write(res.data[0])
        except Exception as e:
            st.error(f"Debug Error: {e}")

# Info message if no chat history
if not st.session_state.chat_history:
    st.info("👋 Welcome! Ask me anything about UNECE WP.29 regulations and working documents.")
    
    # Suggested questions
    st.markdown("### 💭 Suggested Questions")
    
    suggestions = [
        "What are the latest amendments to Regulation No. 48?",
        "Summarize the recent discussions on Autonomous Vehicle Signalling Requirements (AVSR)",
        "What are the proposals from the Special Interest Group on Glare?",
        "Find documents submitted by Italy in the last session"
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 2].button(suggestion, key=f"sugg_{i}"):
            st.session_state.input_text = suggestion
            st.rerun()
