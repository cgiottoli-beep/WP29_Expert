"""
Page 2: Smart Ingestion
AI-powered PDF upload and metadata extraction
"""
import streamlit as st
from supabase_client import SupabaseClient
from pdf_processor import PDFProcessor
from gemini_client import GeminiClient
from embedding_service import EmbeddingService
from config import Config
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Smart Ingestion", page_icon="📤", layout="wide")

from auth_utils import require_auth, check_permission
require_auth()

if not check_permission('collaborator'):
    st.error("⛔ Access Denied: You need at least 'Collaborator' privileges to view this page.")
    st.image("https://media.giphy.com/media/njYrp176NnVIn3rfkp/giphy.gif")
    st.stop()



st.title("📤 Smart Ingestion")
st.markdown("Upload PDFs with AI-powered metadata extraction")

# Session state for uploaded files
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = []

# Show success message if exists (from previous save)
if 'save_success_message' in st.session_state:
    st.success(st.session_state.save_success_message)
    del st.session_state.save_success_message

# Show error messages if exists (from previous save)
if 'save_error_messages' in st.session_state:
    st.warning(f"⚠️ Saved {st.session_state.save_success_count}/{st.session_state.save_total_count} documents. Some errors occurred:")
    for error in st.session_state.save_error_messages:
        st.error(error)
    del st.session_state.save_error_messages
    del st.session_state.save_success_count
    del st.session_state.save_total_count

# ... (imports remain same)

# Tabs
tab1, tab2 = st.tabs(["📄 Application Documents", "🗣️ Interpretations"])

# ============================================================================
# TAB 1: APPLICATION DOCUMENTS (Existing Logic)
# ============================================================================
with tab1:
    st.markdown("### Upload standard UNECE documents (proposals, reports)")
    
    with st.expander("ℹ️ How it works", expanded=False):
        st.markdown("""
        1. **Select Context**: Choose the working group or regulation this document belongs to.
        2. **Upload PDF**: The system will automatically extract the title, symbol, and date.
        3. **Review & Save**: Verify the extracted metadata and save to the database.
        """)

    # 1. Context Selection
    st.markdown("#### 1. Target Session")
    col1, col2 = st.columns(2)
    selected_session_id = None
    
    with col1:
        # Working Group
        try:
            groups = SupabaseClient.get_all_groups()
            group_options = {g['id']: f"{g['full_name']} ({g['type']})" for g in groups}
            selected_group_id = st.selectbox("Working Group", options=list(group_options.keys()), format_func=lambda x: group_options[x], key="doc_group_select")
        except Exception as e:
            st.error(f"Error loading groups: {e}")
            selected_group_id = None
            
    with col2:
        # Session
        if selected_group_id:
            try:
                sessions = SupabaseClient.get_sessions_by_group(selected_group_id)
                sessions.sort(key=lambda s: (s['year'], s['code']), reverse=True)
                if not sessions:
                    st.warning("No sessions found.")
                else:
                    session_options = {s['id']: f"{s['code']} ({s['year']})" for s in sessions}
                    selected_session_id = st.selectbox("Session", options=list(session_options.keys()), format_func=lambda x: session_options[x], key="doc_session_select")
            except Exception as e:
                st.error(f"Error loading sessions: {e}")

    st.markdown("---")

    # 2. Bulk Upload
    st.markdown("#### 2. Upload Documents")
    uploaded_files = st.file_uploader("Drag & Drop multiple PDFs", type="pdf", accept_multiple_files=True, key="bulk_uploader")
    
    # Session state for batch processing
    if 'bulk_results' not in st.session_state:
        st.session_state.bulk_results = []
        
    # PROCESS BUTTON
    if uploaded_files and st.button(f"⚡ Extract Metadata for {len(uploaded_files)} Files"):
        st.session_state.bulk_results = [] # Reset
        progress_bar = st.progress(0)
        status_box = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            status_box.info(f"Processing {idx+1}/{len(uploaded_files)}: {file.name}")
            try:
                # Read bytes
                file.seek(0)
                file_bytes = file.read()
                file.seek(0) # Reset for later
                
                # Extract Text
                text = PDFProcessor.extract_first_page(file_bytes)
                
                # Extract Metadata
                meta = GeminiClient.extract_metadata(text)
                
                # Auto-detect Doc Type - MUST match DB constraint
                # Valid values: Report, Agenda, Adopted Proposals, Formal, Informal
                doc_type_val = meta.get('doc_type') or 'Formal'
                ai_type = doc_type_val.lower()
                
                if 'report' in ai_type:
                    norm_type = "Report"
                elif 'agenda' in ai_type:
                    norm_type = "Agenda"
                elif 'adopted' in ai_type:
                    norm_type = "Adopted Proposals"
                elif 'informal' in ai_type:
                    norm_type = "Informal"
                else:
                    # Default to Formal for proposals, working docs, etc.
                    norm_type = "Formal"
                
                # Auto-detect Regulation ID
                ai_regs = meta.get('mentioned_regulations') or []
                
                # PRE-GENERATE chunks immediately while bytes are fresh
                chunks = []
                try:
                    chunks = PDFProcessor.extract_chunks(file_bytes, chunk_size=1000)
                    # Don't use status_box - it gets overwritten. Just store the count
                except Exception as chunk_err:
                    # Store error for display later
                    chunks = []
                
                # Store - save BOTH bytes and pre-generated chunks
                st.session_state.bulk_results.append({
                    "file_name": file.name,
                    "file_bytes": bytes(file_bytes),  # For upload
                    "pre_chunks": chunks,  # For embedding (already extracted)
                    "symbol": meta.get('symbol') or '',
                    "title": meta.get('title') or '',
                    "author": meta.get('author') or 'Unknown',
                    "doc_type": norm_type,
                    "regulations": ", ".join(ai_regs) if ai_regs else "",
                    "date": datetime.now().date(),
                    "selected": True,
                    "embed": len(chunks) > 0  # Only embed if chunks exist
                })
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
                
        status_box.success("Extraction Complete! Review results below.")
        
    # 3. Review & Save
    if st.session_state.bulk_results:
        st.markdown("#### 3. Review & Save")
        
        # Display as editable df? Or just list of Expanders.
        # Data Editor is cleaner for bulk.
        
        # Prepare Data for Editor
        # We need to create a list of dicts that st.data_editor can handle, 
        # but we need to map back to file objects.
        # Simpler approach: List of Expanders with forms.
        
        with st.form("bulk_save_form"):
            count = 0
            for i, result in enumerate(st.session_state.bulk_results):
                with st.expander(f"📄 {result['file_name']} -> {result['symbol']}", expanded=True):
                    result['selected'] = st.checkbox("Include this file", value=result['selected'], key=f"sel_{i}")
                    
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        result['symbol'] = st.text_input("Symbol", value=result['symbol'], key=f"sym_{i}")
                        # Valid DB values: Report, Agenda, Adopted Proposals, Formal, Informal
                        valid_types = ["Formal", "Informal", "Report", "Agenda", "Adopted Proposals"]
                        current_type = result['doc_type'] if result['doc_type'] in valid_types else "Formal"
                        result['doc_type'] = st.selectbox("Type", valid_types, index=valid_types.index(current_type), key=f"typ_{i}")
                    with c2:
                        result['title'] = st.text_input("Title", value=result['title'], key=f"tit_{i}")
                        result['author'] = st.text_input("Author", value=result['author'], key=f"aut_{i}")
                    with c3:
                         result['embed'] = st.checkbox("Generate Search Embeddings", value=result['embed'], key=f"emb_{i}")
                         # Show chunk count
                         chunk_count = len(result.get('pre_chunks', []))
                         if chunk_count > 0:
                             st.caption(f"✓ {chunk_count} chunks extracted")
                         else:
                             st.caption("⚠ No chunks extracted")
                         # Editable regulations field
                         result['regulations'] = st.text_input("Regulations", value=result['regulations'], key=f"reg_{i}", help="Comma-separated, e.g. R48, R149")
                
                count += 1
            
            if st.form_submit_button("💾 Save Selected Documents"):
                if not selected_session_id:
                    st.error("Please select a Session above.")
                else:
                    success_count = 0
                    progress_save = st.progress(0)
                    
                    to_save = [r for r in st.session_state.bulk_results if r['selected']]
                    
                    for idx, item in enumerate(to_save):
                        try:
                            # Get bytes for upload
                            bytes_data = item['file_bytes']
                            
                            # Step 1: Sanitize filename and upload
                            import re
                            # Ensure symbol is string, fallback to 'Unknown' if empty
                            clean_symbol = str(item['symbol'] or 'Unknown')
                            safe_symbol = re.sub(r'[/\\:*?"<>|]', '-', clean_symbol)
                            path = f"documents/{safe_symbol}.pdf"
                            
                            # Step 2: Upload to Supabase Storage
                            try:
                                url = SupabaseClient.upload_file(path, bytes_data)
                            except Exception as upload_err:
                                raise Exception(f"Upload failed: {upload_err}")
                            
                            # Step 3: Create DB Record
                            try:
                                doc_response = SupabaseClient.create_document(
                                    session_id=selected_session_id,
                                    symbol=item['symbol'],
                                    title=item['title'],
                                    author=item['author'],
                                    doc_type=item['doc_type'],
                                    file_url=url,
                                    submission_date=item['date'].strftime("%Y-%m-%d")
                                )
                                doc_id = doc_response['id']  # Extract ID from response
                            except Exception as db_err:
                                raise Exception(f"DB create failed: {db_err}")
                            
                            # Step 4: Store pre-generated embeddings
                            if item['embed'] and len(item.get('pre_chunks', [])) > 0:
                                try:
                                    chunks = item['pre_chunks']
                                    authority_level = 10 if item['doc_type'] in ['Report', 'Agenda'] else 1
                                    
                                    # Create progress display
                                    total_chunks = len(chunks)
                                    emb_progress = st.progress(0)
                                    emb_status = st.empty()
                                    
                                    embeddings_created = 0
                                    for chunk_idx, chunk in enumerate(chunks):
                                        if not chunk.strip():
                                            continue
                                        
                                        # Show progress
                                        emb_status.text(f"Generating embedding {chunk_idx + 1}/{total_chunks} for {item['symbol']}...")
                                        
                                        # Generate embedding
                                        embedding = GeminiClient.generate_embedding(chunk)
                                        # Store
                                        SupabaseClient.create_embedding(
                                            source_id=doc_id,
                                            source_type="document",
                                            content_chunk=chunk,
                                            embedding=embedding,
                                            authority_level=authority_level
                                        )
                                        embeddings_created += 1
                                        
                                        # Update progress
                                        emb_progress.progress((chunk_idx + 1) / total_chunks)
                                    
                                    # Clear progress indicators
                                    emb_progress.empty()
                                    emb_status.empty()
                                    
                                    st.caption(f"✓ Stored {embeddings_created} embeddings for {item['symbol']}")
                                except Exception as emb_err:
                                    st.warning(f"Embedding storage failed for {item['symbol']}: {emb_err}")
                                
                            success_count += 1
                            progress_save.progress((idx + 1) / len(to_save))
                            
                        except Exception as e:
                            st.error(f"Failed to save {item['file_name']}: {e}")
                            
                    st.success(f"Successfully saved {success_count} documents!")
                    # Clear
                    st.session_state.bulk_results = []
                    # st.rerun()
    
    # ... (BATCH METADATA UPDATE logic at the bottom of Tab 1)

# ============================================================================
# TAB 2: INTERPRETATIONS
# ============================================================================
with tab2:
    st.markdown("### Upload Interpretations (Ministries, TAAM, Internal)")
    
    # 1. Issuer Selection
    st.markdown("#### 1. Issuer Details")
    try:
        issuers = SupabaseClient.get_all_issuers()
        issuer_options = {i['id']: f"{i['name']} ({i['code']})" for i in issuers}
        
        col_i1, col_i2 = st.columns([3, 1])
        with col_i1:
            selected_issuer_id = st.selectbox("Select Issuer", options=list(issuer_options.keys()), format_func=lambda x: issuer_options[x], key="interp_issuer")
        with col_i2:
            with st.expander("➕ Add New Issuer"):
                new_issuer_name = st.text_input("Name")
                new_issuer_code = st.text_input("Code (e.g. E5)")
                new_issuer_type = st.selectbox("Type", ["Ministry", "Group", "Internal"])
                if st.button("Create Issuer"):
                    if new_issuer_name:
                        SupabaseClient.create_issuer(new_issuer_name, new_issuer_code, new_issuer_type)
                        st.success("Issuer created! Refresh page to see.")
                    else:
                        st.error("Name required")
    except Exception as e:
        st.error(f"Error loading issuers: {e}")

    st.markdown("---")
    
    # 2. Interpretation Metadata
    st.markdown("#### 2. Metadata")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        i_title = st.text_input("Title", key="interp_title")
        i_date = st.date_input("Issue Date", key="interp_date", min_value=datetime(1950, 1, 1))
        i_status = st.selectbox("Status", ["draft", "final", "superseded"], key="interp_status")
    with col_m2:
        i_reg_ref = st.text_input("Regulation Reference (e.g. R48.09)", key="interp_reg")
        i_visibility = st.radio("Visibility", ["Public", "Private"], horizontal=True, key="interp_vis")
        is_public_bool = (i_visibility == "Public")
    
    i_comments = st.text_area("Comments / Summary", key="interp_comments")

    # Define callback for auto-fill
    def auto_fill_metadata():
        uploaded_pdf = st.session_state.get('interp_file')
        if not uploaded_pdf:
            return
            
        try:
             # We can't use st.spinner inside a callback easily, but the operation should be fast enough or we accept a freeze.
             # Alternatively we just proceed.
             pdf_bytes_fill = uploaded_pdf.read()
             uploaded_pdf.seek(0) # Reset pointer
             
             # Use full text to catch all mentioned regulations
             text_fill = PDFProcessor.extract_all_text(pdf_bytes_fill)
             meta = GeminiClient.extract_metadata(text_fill)
             
             # Safely update session state
             st.session_state['interp_title'] = meta.get('title', '') or ''
             
             # Clean and deduplicate regulations
             regs = meta.get('mentioned_regulations', [])
             if isinstance(regs, list):
                 # Deduplicate preserving order
                 unique_regs = sorted(list(set(regs)), key=regs.index)
                 st.session_state['interp_reg'] = ", ".join(unique_regs)
             else:
                 st.session_state['interp_reg'] = str(regs)
             # Set a flag to show success message on next run
             st.session_state['auto_fill_success'] = True
             
        except Exception as e:
            st.session_state['auto_fill_error'] = str(e)

    # 3. Content (Hybrid)
    st.markdown("#### 3. Content")
    content_type = st.radio("Content Source", ["PDF File", "Text-only / Transcription"], horizontal=True)
    
    i_file = None
    i_text = None
    
    if content_type == "PDF File":
        i_file = st.file_uploader("Upload PDF", type=['pdf'], key="interp_file")
        
        # AI Extraction for Interpretations (Button triggers callback)
        st.button("✨ Auto-Fill Metadata from PDF", on_click=auto_fill_metadata)
        
        if st.session_state.get('auto_fill_success'):
            st.success("Metadata extracted! Review fields above.")
            # Clear flag to avoid persistent message
            st.session_state['auto_fill_success'] = False
            
        if st.session_state.get('auto_fill_error'):
            st.error(f"Extraction failed: {st.session_state.get('auto_fill_error')}")
            st.session_state['auto_fill_error'] = None

    else:
        st.info("Paste the full content of the email or interpretation note here for searching.")
        i_text = st.text_area("Full Text Content", height=300, key="interp_text_content")

    # 4. Save
    st.markdown("---")
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
         generate_interp_embeddings = st.checkbox(
            "Generate embeddings for AI Search",
            value=True,
            help="Enable to make this interpretation searchable with AI Assistant",
            key="interp_emb_check"
        )
    
    with col_s2:
        if st.button("💾 Save Interpretation", type="primary"):
            if not i_title or not selected_issuer_id:
                st.error("Title and Issuer are required.")
                if not i_title and content_type == "PDF File" and i_file:
                     st.warning("Tip: Use 'Auto-Fill Metadata' to extract title from PDF.")
            else:
                status_box = st.empty()
                with st.spinner("Saving..."):
                    try:
                        # 1. Upload File (if PDF)
                        file_url = None
                        if i_file:
                            file_bytes = i_file.read()
                            # Reset pointer just in case
                            i_file.seek(0)
                            safe_name = i_file.name.replace(" ", "_").replace("/", "-")
                            path = f"interpretations/{datetime.now().year}/{safe_name}"
                            # Ensure unique path if needed, but Supabase handles overwrites or we can append timestamp
                            # Adding timestamp to be safe
                            timestamp = int(datetime.now().timestamp())
                            path = f"interpretations/{datetime.now().year}/{timestamp}_{safe_name}"
                            
                            file_url = SupabaseClient.upload_file(path, file_bytes)
                        
                        # 2. Save Record
                        interp = SupabaseClient.create_interpretation(
                            title=i_title,
                            issuer_id=selected_issuer_id,
                            issue_date=i_date.isoformat(),
                            status=i_status,
                            regulation_mentioned=i_reg_ref,
                            comments=i_comments,
                            content_text=i_text,
                            file_url=file_url,
                            is_public=is_public_bool
                        )
                        
                        # 3. Generate Embeddings
                        if generate_interp_embeddings and interp and interp.get('id'):
                            status_box.info("Generating embeddings...")
                            progress_bar = st.progress(0)
                            
                            def update_progress(current, total):
                                progress = min(current / total, 1.0)
                                progress_bar.progress(progress)
                                status_box.info(f"Generating embeddings: Chunk {current}/{total}")

                            emb_count = 0
                            last_error = None
                            
                            if i_text:
                                emb_count, last_error = EmbeddingService.generate_interpretation_embeddings(
                                    interp['id'], text_content=i_text, progress_callback=update_progress
                                )
                            elif i_file:
                                # Ensure we are reading from the start of the file
                                i_file.seek(0)
                                pdf_data = i_file.read()
                                
                                # Debug logging
                                if len(pdf_data) == 0:
                                    status_box.error("Error: Read 0 bytes from PDF file.")
                                else:
                                    status_box.info(f"Processing PDF ({len(pdf_data)} bytes)...")
                                    emb_count, last_error = EmbeddingService.generate_interpretation_embeddings(
                                        interp['id'], pdf_bytes=pdf_data, progress_callback=update_progress
                                    )
                            
                            progress_bar.empty()
                            if emb_count > 0:
                                status_box.success(f"Generated {emb_count} search chunks.")
                            else:
                                if last_error:
                                    status_box.error(f"Error generating embeddings: {last_error}")
                                else:
                                    status_box.warning("Generated 0 search chunks. The PDF might be scanned or image-only.")

                        st.success("✅ Interpretation saved successfully!")
                        # Optional: clear form logic could go here but hard in Streamlit without clear_on_submit or rerun
                        
                    except Exception as e:
                        st.error(f"Error saving: {e}")




