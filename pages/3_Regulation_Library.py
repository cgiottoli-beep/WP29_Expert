"""
Page 3: Regulation Library
Upload and explore regulation versions
"""
import streamlit as st
from supabase_client import SupabaseClient
from embedding_service import EmbeddingService
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Regulation Library", page_icon="📕", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("📕 Regulation Library")
st.markdown("Manage official consolidated regulations")

# Helper function to get signed URL for better PDF viewing
def get_viewable_url(file_url):
    """Convert public URL to signed URL for better compatibility"""
    if file_url:
        return SupabaseClient.get_signed_url(file_url)
    return None

tabs = st.tabs(["📚 Explorer", "➕ Upload New"])

# ============================================================================
# TAB 1: EXPLORER
# ============================================================================

with tabs[0]:
    st.markdown("### Regulation Explorer")
    
    try:
        regulations = SupabaseClient.get_all_regulations()
        
        if not regulations:
            st.info("No regulations found. Upload your first regulation in the 'Upload New' tab.")
        else:
            # Display each regulation with its versions
            for reg in regulations:
                with st.expander(f"**{reg['id']}** - {reg['title']}", expanded=False):
                    st.markdown(f"**Topic:** {reg.get('topic', 'N/A')}")
                    
                    # Get versions
                    versions = SupabaseClient.get_regulation_versions(reg['id'])
                    
                    if versions:
                        # Sort by entry date
                        versions_sorted = sorted(
                            versions,
                            key=lambda x: x.get('entry_date', '1900-01-01'),
                            reverse=True
                        )
                        
                        st.markdown("#### Versions")
                        
                        for ver in versions_sorted:
                            status_icon = "✅" if ver['status'] == 'In Force' else "📋"
                            status_color = "green" if ver['status'] == 'In Force' else "gray"
                            
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                            
                            with col1:
                                st.markdown(f"{status_icon} **{ver['series']}** {ver['revision']}")
                            
                            with col2:
                                st.markdown(f":{status_color}[{ver['status']}]")
                            
                            with col3:
                                st.markdown(f"Entry: {ver.get('entry_date', 'N/A')}")
                            
                            with col4:
                                if ver.get('file_url'):
                                    st.link_button("📄 View", get_viewable_url(ver['file_url']), use_container_width=True)
                    else:
                        st.info("No versions uploaded yet")
    
    except Exception as e:
        st.error(f"Error loading regulations: {e}")

# ============================================================================
# TAB 2: UPLOAD
# ============================================================================

with tabs[1]:
    st.markdown("### Upload New Regulation Version")
    
    # Check if regulation exists or create new
    regulation_option = st.radio(
        "Regulation",
        ["Existing Regulation", "New Regulation"]
    )
    
    if regulation_option == "Existing Regulation":
        try:
            regulations = SupabaseClient.get_all_regulations()
            if not regulations:
                st.warning("No existing regulations. Please select 'New Regulation'.")
                st.stop()
            
            selected_reg = st.selectbox(
                "Select Regulation",
                options=[r['id'] for r in regulations],
                format_func=lambda x: f"{x} - {next(r['title'] for r in regulations if r['id'] == x)}"
            )
            reg_id = selected_reg
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
    else:
        # New regulation
        col1, col2 = st.columns(2)
        with col1:
            reg_id = st.text_input("Regulation ID", placeholder="e.g., R48")
        with col2:
            reg_title = st.text_input("Title", placeholder="e.g., Uniform provisions concerning lighting devices")
        
        reg_topic = st.text_input("Topic", placeholder="e.g., Lighting and signaling")
    
    st.markdown("---")
    
    # Version details
    col1, col2, col3 = st.columns(3)
    
    with col1:
        series = st.text_input("Series", placeholder="e.g., 09 Series")
    
    with col2:
        revision = st.text_input("Revision", placeholder="e.g., Rev. 14")
    
    with col3:
        status = st.selectbox("Status", ["In Force", "Superseded"])
    
    entry_date = st.date_input("Entry into Force Date", value=datetime.now())
    
    # File upload
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    
    generate_embeddings = st.checkbox(
        "Generate embeddings for RAG search",
        value=True,
        help="Make this regulation searchable with AI Assistant"
    )
    
    if st.button("📤 Upload Regulation", type="primary"):
        if regulation_option == "New Regulation":
            if not reg_id or not reg_title:
                st.error("Please fill in Regulation ID and Title")
                st.stop()
        
        if not series or not revision or not uploaded_file:
            st.error("Please fill in all version details and upload a PDF")
            st.stop()
        
        try:
            with st.spinner("Processing..."):
                # Create regulation if new
                if regulation_option == "New Regulation":
                    try:
                        SupabaseClient.create_regulation(
                            reg_id=reg_id,
                            title=reg_title,
                            topic=reg_topic if reg_topic else None
                        )
                        st.success(f"Created regulation: {reg_id}")
                    except Exception as e:
                        st.warning(f"Regulation may already exist: {e}")
                
                # Upload PDF
                pdf_bytes = uploaded_file.read()
                filename = uploaded_file.name
                storage_path = f"REGULATIONS/{reg_id}/{series}/{filename}"
                file_url = SupabaseClient.upload_file(storage_path, pdf_bytes)
                
                # Create version record
                version = SupabaseClient.create_regulation_version(
                    regulation_id=reg_id,
                    series=series,
                    revision=revision,
                    status=status,
                    entry_date=entry_date.isoformat(),
                    file_url=file_url
                )
                
                # Generate embeddings
                if generate_embeddings:
                    st.info("Generating embeddings...")
                    count = EmbeddingService.generate_regulation_embeddings(
                        version['id'],
                        pdf_bytes
                    )
                    st.success(f"Generated {count} embeddings")
                
                st.success(f"✅ Uploaded {reg_id} - {series} {revision}")
                st.balloons()
        
        except Exception as e:
            st.error(f"Error uploading regulation: {e}")
