"""
UNECE WP.29 Intelligent Archive
Main Streamlit application entry point
"""
import requests
import re

import streamlit as st
from supabase_client import SupabaseClient

# Page configuration
st.set_page_config(
    page_title="UNECE WP.29 Archive",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI (Minimal/Clean)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0d47a1; /* UN Blue / Agenda Blue */
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
        text-align: center;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_upcoming_events():
    """Fetch upcoming meetings from GlobalAutoRegs with caching"""
    url = "https://globalautoregs.com"
    try:
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        if response.status_code == 200:
            html = response.text
            # Regex to find links in the table
            # Pattern matches <a href="/meetings/..."> Text </a>
            pattern = r'<a href="(/meetings/\d+)">\s*(.*?)\s*</a>'
            matches = re.findall(pattern, html)
            
            events = []
            seen_links = set()
            
            for link, text in matches:
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                # Clean text
                text_clean = text.replace('\n', ' ').replace('\t', ' ').strip()
                
                # Try to extract date if present (Format usually: Title | Session | Date)
                parts = text_clean.split('|')
                if len(parts) >= 3:
                     # e.g. "Working Party... | Session 24 | 19-23 Jan"
                    title = parts[0].strip()
                    date = parts[-1].strip() # Take the last part as date
                elif len(parts) == 2:
                     title = parts[0].strip()
                     date = parts[1].strip()
                else:
                    title = text_clean
                    date = "Upcoming"
                
                events.append({
                    "title": title,
                    "date": date,
                    "url": url + link
                })
                
                if len(events) >= 5: # Limit to 5
                    break
            return events
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []
    return []

from auth_utils import init_auth, login_form, render_sidebar

def main():
    """Main application page"""
    
    # Initialize Auth
    init_auth()
    
    # Render Sidebar (Handles User Status & Navigation)
    render_sidebar()
    
    # Show Login if not authenticated
    if not st.session_state['authenticated']:
        login_form()
        return

    # If authenticated, show welcome info
    # (Sidebar status is handled by render_sidebar)

    
    # Simple Text Header (No Logo)
    st.markdown('<div class="main-header">UNECE WP.29 Intelligent Archive</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Document Management System for UN Vehicle Regulations</div>', 
                unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏛️ Structure")
        st.markdown("""
        - Manage Groups (WP29, GRs, IWGs)
        - Create Sessions
        - Organize hierarchy
        """)
        if st.button("Go to Admin & Structure", use_container_width=True):
            st.switch_page("pages/1_Admin_Structure.py")
    
    with col2:
        st.markdown("### 📄 Documents")
        st.markdown("""
        - Smart PDF ingestion
        - AI metadata extraction
        - Session document view
        """)
        if st.button("Upload Documents", use_container_width=True):
            st.switch_page("pages/2_Smart_Ingestion.py")
    
    with col3:
        st.markdown("### 🤖 AI Assistant")
        st.markdown("""
        - RAG-powered chatbot
        - Search regulations
        - Generate reports
        """)
        if st.button("Open AI Assistant", use_container_width=True):
            st.switch_page("pages/5_AI_Assistant.py")
    
    st.markdown("---")
    
    # Upcoming Events Section
    event_col1, event_col2 = st.columns([4, 1])
    with event_col1:
        st.markdown("### 📅 Upcoming WP.29 Meetings")
        st.caption("Sourced from GlobalAutoRegs.com")
    with event_col2:
        if st.button("🔄 Update Events", help="Force refresh from source"):
            fetch_upcoming_events.clear()
            st.rerun()
    
    with st.spinner("Fetching schedule..."):
        events = fetch_upcoming_events()
        
    if events:
        # Display as cards in columns or a nice list
        for event in events:
            with st.container():
                st.markdown(f"**{event['date']}** — [{event['title']}]({event['url']})")
    else:
        st.info("Could not fetch live schedule.")
        st.markdown("[View Official Calendar](https://globalautoregs.com/calendar)")
    
    st.markdown("---")
    
    # System status
    st.markdown("### 📊 System Status")
    
    try:
        # Try to fetch some data to verify connection
        groups = SupabaseClient.get_all_groups()
        
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            st.metric("Database", "✅ Connected")
        
        with status_col2:
            st.metric("Total Groups", len(groups))
        
        with status_col3:
            st.metric("AI Engine", "✅ Gemini Ready")
        
    except Exception as e:
        st.error(f"⚠️ System Error: {str(e)}")
        st.info("""
        **First-time setup required:**
        1. Run `init_database.sql` in your Supabase SQL Editor
        2. Ensure pgvector extension is enabled
        3. Verify .env configuration
        """)
    
    # Quick start guide
    st.markdown("---")
    st.markdown("### 🚀 Quick Start")
    
    with st.expander("📖 Getting Started Guide"):
        st.markdown("""
        **Step 1: Initialize Structure**
        - Go to *Admin & Structure* page
        - The system will auto-create 'WP29' root group on first run
        - Add your working groups (GRE, GRVA, etc.)
        
        **Step 2: Create Sessions**
        - For each group, create sessions with year and code
        - Example: GRE Session 90, Year 2024
        
        **Step 3: Upload Documents**
        - Go to *Smart Ingestion* page
        - Select Group and Session
        - Drag & drop PDF files
        - AI will extract metadata automatically
        
        **Step 4: Explore & Search**
        - Use *Search & Session View* to browse documents
        - Use *AI Assistant* to ask questions
        - Generate session reports with *Report Generator*
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #999;">UNECE WP.29 Archive • Built with Streamlit + Supabase + Google Gemini</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
