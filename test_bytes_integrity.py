"""
Test if bytes stored in session state remain valid
"""
import streamlit as st
from pdf_processor import PDFProcessor

# Simulate what happens in Smart Ingestion
st.title("Bytes Integrity Test")

uploaded = st.file_uploader("Upload a PDF", type=['pdf'])

if uploaded:
    # Read bytes
    uploaded.seek(0)
    file_bytes = uploaded.read()
    
    st.write(f"Read {len(file_bytes)} bytes")
    
    # Test immediate extraction
    try:
        chunks = PDFProcessor.extract_chunks(file_bytes)
        st.success(f"✅ Direct extraction: {len(chunks)} chunks")
    except Exception as e:
        st.error(f"❌ Direct extraction failed: {e}")
    
    # Store in session state
    if 'stored_bytes' not in st.session_state:
        st.session_state.stored_bytes = file_bytes
        st.write("Stored bytes in session_state")
    
    # Try extracting from session state
    if st.button("Extract from Session State"):
        try:
            st.write(f"Session state has {len(st.session_state.stored_bytes)} bytes")
            chunks = PDFProcessor.extract_chunks(st.session_state.stored_bytes)
            st.success(f"✅ Session state extraction: {len(chunks)} chunks")
        except Exception as e:
            st.error(f"❌ Session state extraction failed: {e}")
            st.write(f"Bytes type: {type(st.session_state.stored_bytes)}")
