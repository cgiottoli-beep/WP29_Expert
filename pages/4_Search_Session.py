"""
Page 4: Search & Session View
Browse and filter documents
"""
import streamlit as st
from supabase_client import SupabaseClient
from embedding_service import EmbeddingService
from config import Config
import pandas as pd
import time

def get_type_badge(doc_type):
    if not doc_type:
        return ""
    
    # Colors: (background, text)
    colors = {
        "Formal": ("#a5d6a7", "#1b5e20"),       # Green (darker bg, dark text)
        "Informal": ("#fff8c4", "#f57f17"),     # Yellow (light yellow bg, dark orange text)
        "Agenda": ("#d6eafd", "#0d47a1"),       # Blue
        "Report": ("#d6eafd", "#0d47a1"),       # Blue
        "Adopted Proposals": ("#e1bee7", "#4a148c") # Purple
    }
    
    # Default Gray
    bg, color = colors.get(doc_type, ("#f5f5f5", "#616161"))
    
    return f'<span style="background-color: {bg}; color: {color}; padding: 3px 8px; border-radius: 10px; font-size: 0.85em; font-weight: 600; white-space: nowrap;">{doc_type}</span>'

st.set_page_config(page_title="Search & Session View", page_icon="🔍", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("🔍 Search & Session View")
st.markdown("Browse documents by session, group, or regulation")

# ============================================================================
# FILTERS SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 🔎 Filters")
    
    if st.button("🧹 Clear All Filters", type="secondary", use_container_width=True):
        keys_to_clear = ['filter_group_main', 'filter_session_main', 'filter_year_main', 'filter_type_main', 'search_text_main']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Group filter
    try:
        groups = SupabaseClient.get_all_groups()
        if not groups:
            st.error("No groups.")
            st.stop()
        
        # ... (Group/Session/Regulation filters remain)
    except Exception as e:
        st.error(f"Error loading filters: {e}")

    st.markdown("---")
    with st.expander("⚙️ Manage Embeddings"):
        st.markdown("Check for documents lacking AI index.")
        if st.button("🔄 Scan Missing"):
            with st.spinner("Scanning..."):
                missing = SupabaseClient.get_documents_without_embeddings()
                st.session_state['missing_docs'] = missing
        
        if 'missing_docs' in st.session_state:
            missing = st.session_state['missing_docs']
            if not missing:
                st.success("All indexed!")
            else:
                st.warning(f"Found {len(missing)} missing.")
                if st.button(f"🚀 Embed {len(missing)} Docs"):
                    progress = st.progress(0)
                    status = st.empty()
                    success_gen = 0
                    for i, doc in enumerate(missing):
                        status.text(f"Processing {doc.get('symbol')}...")
                        try:
                            # Parse path from URL
                            file_url = doc.get('file_url') or ""
                            # Robust path extraction
                            if "unece-archive/" in file_url:
                                path = file_url.split("unece-archive/")[-1].split("?")[0]
                            elif file_url.startswith("http"):
                                # If direct link without known bucket structure, try to standard parse
                                path = file_url
                            else:
                                path = file_url
                                
                            if path:
                                pdf_bytes = SupabaseClient.download_file(path)
                                EmbeddingService.generate_document_embeddings(
                                    doc['id'], pdf_bytes, doc.get('doc_type', 'Unknown')
                                )
                                success_gen += 1
                        except Exception as e:
                            print(f"Failed {doc.get('symbol')}: {e}")
                        progress.progress((i+1)/len(missing))
                    st.success(f"Embedded {success_gen} docs!")
                    st.session_state.pop('missing_docs')
                    st.rerun()


    try:
        groups = SupabaseClient.get_all_groups()
        group_options = ["All"] + [g['id'] for g in groups]
        
        # Check for navigation filter
        default_index = 0
        if 'filter_group' in st.session_state:
            target_group = st.session_state.get('filter_group')
            if target_group in group_options:
                default_index = group_options.index(target_group)
            # Clear filter after use so user can change it freely
            del st.session_state['filter_group']
            
        selected_group = st.selectbox("Group", group_options, index=default_index, key="filter_group_main")
    except:
        selected_group = "All"
    
    # Session filter
    if selected_group != "All":
        try:
            sessions = SupabaseClient.get_sessions_by_group(selected_group)
            session_options = ["All"] + [f"Session {s['code']} ({s['year']})" for s in sessions]
            selected_session_str = st.selectbox("Session", session_options, key="filter_session_main")
            
            if selected_session_str != "All":
                selected_session = sessions[session_options.index(selected_session_str) - 1]
            else:
                selected_session = None
        except:
            selected_session = None
    else:
        selected_session = None
    
    # Year filter
    try:
        # Get unique years from all sessions if no group selected, or group sessions if selected
        if selected_group != "All":
             # Sessions already loaded above
             available_years = sorted(list(set(s['year'] for s in sessions)), reverse=True)
        else:
             # Need to fetch all sessions to get years
             # Ideally SupabaseClient should have a get_unique_years method, but for now:
             all_sessions_resp = SupabaseClient.get_client().table("sessions").select("year").execute()
             available_years = sorted(list(set(s['year'] for s in all_sessions_resp.data)), reverse=True)
             
        year_options = ["All"] + available_years
        selected_year = st.selectbox("Year", year_options, key="filter_year_main")
    except:
        selected_year = "All"
    
    # Type filter
    selected_type = st.selectbox(
        "Document Type",
        ["All", "Report", "Agenda", "Adopted Proposals", "Formal", "Informal"],
        key="filter_type_main"
    )
    
    # Free text search
    st.markdown("---")
    search_text = st.text_input(
        "🔍 Search",
        placeholder="Search in symbol, title, author, regulation...",
        help="Search across symbol, title, author, and regulation mentioned fields",
        key="search_text_main"
    )

# ============================================================================
# FETCH AND DISPLAY DOCUMENTS
# ============================================================================

# Helper function to get signed URL for better PDF viewing
def get_viewable_url(file_url):
    """Convert public URL to signed URL for better compatibility"""
    if file_url:
        return SupabaseClient.get_signed_url(file_url)
    return None


try:
    # Pagination State
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Reset page when filters change (using a hash of filters to detect change would be ideal, 
    # but for now we rely on explicit 'on_change' or just simple reset if needed. 
    # A simple approach: if we detect a search/filter interaction, we reset.
    # We'll handle this by buttons/inputs updating state.)
    
    ITEMS_PER_PAGE = 50
    
    # Build filter dictionary
    filters = {}
    
    if selected_session:
        filters['session_id'] = selected_session['id']
    
    if selected_year != "All":
        filters['year'] = selected_year
    
    if selected_type != "All":
        filters['doc_type'] = selected_type
        
    if selected_group != "All" and not selected_session:
        filters['group_id'] = selected_group
    
    # Fetch Counts and Data
    try:
        # Get Total Count
        total_items = SupabaseClient.get_documents_count(filters, search_text)
        total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        
        # Ensure page is valid
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1
            
        offset = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        
        # Fetch Page Data
        documents = SupabaseClient.search_documents(
            filters, 
            search_text, 
            limit=ITEMS_PER_PAGE, 
            offset=offset
        )
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        documents = []
        total_items = 0
    
    st.markdown(f"**Found {total_items} documents**")
    
    if not documents:
        st.info("No documents found. Try adjusting filters.")
    else:
        
        # Separate by type (for display only)
        # Note: Pagination applies to the TOTAL result set, so we might show fewer of one type on a page.
        reports_agendas = [d for d in documents if d['doc_type'] in ['Report', 'Agenda', 'Adopted Proposals']]
        working_docs = [d for d in documents if d['doc_type'] in ['Formal', 'Informal']]
        
        # Separate by type
        reports_agendas = [d for d in documents if d['doc_type'] in ['Report', 'Agenda', 'Adopted Proposals']]
        working_docs = [d for d in documents if d['doc_type'] in ['Formal', 'Informal']]
        
        # ====================================================================
        # EMBEDDING STATUS CHECK
        # ====================================================================
        
        # ====================================================================
        # EMBEDDING STATUS CHECK
        # ====================================================================
        
        # Get counts of embeddings for each document
        embedding_counts = {}
        debug_emb_errors = []
        try:
            # Use Admin Client to bypass RLS for status checks
            # This ensures we see the true count even if the user doesn't own the records
            try:
                client = SupabaseClient.get_admin_client()
            except Exception:
                # Fallback to normal client if Service Key not configured (local dev without .env?)
                client = SupabaseClient.get_client()
            
            # Optimization: Only check status for the documents we currently have loaded
            current_doc_ids = [d['id'] for d in documents] if documents else []
            
            if current_doc_ids:
                # Try optimized RPC first (single query for all docs)
                try:
                    rpc_response = client.rpc("get_embedding_counts", {
                        "doc_ids": current_doc_ids
                    }).execute()
                    
                    # Parse RPC results
                    for row in rpc_response.data:
                        embedding_counts[str(row['source_id'])] = row['count']
                        
                except Exception as rpc_err:
                    # Fallback to individual queries if RPC not available
                    # (Run optimize_embedding_counts.sql in Supabase to enable RPC)
                    for doc_id in current_doc_ids:
                        try:
                            emb_response = client.table("embeddings") \
                                .select("source_id", count="exact") \
                                .eq("source_id", doc_id) \
                                .limit(1) \
                                .execute()
                            
                            if emb_response.count and emb_response.count > 0:
                                embedding_counts[str(doc_id)] = emb_response.count
                        except Exception as doc_err:
                            debug_emb_errors.append(f"Doc {doc_id}: {str(doc_err)}")
                    
                except Exception as e:
                    # Fallback or error logging
                    print(f"Error fetching embedding counts: {e}")
                    debug_emb_errors.append(f"General: {str(e)}")
                
        except Exception as e:
            st.error(f"Error fetching embedding status: {e}")
            embedding_counts = {}

        if debug_emb_errors:
            st.warning(f"⚠️ Some embedding status checks failed ({len(debug_emb_errors)} errors)")

        # LEGEND
        st.markdown("### 📊 Status Legend")
        st.caption("🟢 Ready (Chunks) | ⚡ Process")

        # Statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Documents", total_items) # Use total server count
        
        with col2:
            st.metric("Reports/Agendas", len([d for d in documents if d['doc_type'] in ['Report', 'Agenda', 'Adopted Proposals']]))
        
        with col3:
            st.metric("Working Docs", len([d for d in documents if d['doc_type'] in ['Formal', 'Informal']]))
        
        st.markdown("---")

        # ====================================================================
        # OUTCOMES & AGENDA SECTION
        # ====================================================================
        
        
        if reports_agendas:
            st.markdown("### 📋 Outcomes & Agenda")
            st.markdown("*Session reports and agendas (high authority)*")
            
            # Edit Dialog for Reports... (omitted)
            if st.session_state.get('editing_report_id'):
                 # ... existing code ...
                 pass

            # ... (omitted delete dialog)

            
             # Display Reports/Agendas with action buttons
            for idx, doc in enumerate(reports_agendas):
                # Adjusted columns: Wider Symbol (2.5), Smaller Actions (0.8)
                cols = st.columns([0.4, 2.5, 3, 0.8, 1.2, 1, 0.8])
                
                # Status Column
                with cols[0]:
                    count = embedding_counts.get(doc['id'], 0)
                    if count > 0:
                        # Compact badge style
                        st.markdown(f"<span style='background-color:#e6fffa; color:#047857; padding:2px 6px; border-radius:10px; font-size:0.8em; font-weight:bold;'>{count}</span>", unsafe_allow_html=True)
                    elif not doc.get('file_url'):
                        st.write(" ")
                    else:
                        if st.button("⚡", key=f"emb_rep_{idx}", help="Generate Embeddings"):
                            try:
                                with st.spinner("Wait..."):
                                    # Download file
                                    if Config.STORAGE_BUCKET in doc['file_url']:
                                        file_path = doc['file_url'].split(f'/{Config.STORAGE_BUCKET}/')[-1]
                                    else:
                                        file_path = doc['file_url']
                                    
                                    pdf_bytes = SupabaseClient.download_file(file_path)
                                    
                                    # Generate embeddings (with progress bar potentially, but spinner is okay for now)
                                    count = EmbeddingService.generate_document_embeddings(
                                        doc['id'], pdf_bytes, doc['doc_type']
                                    )
                                    
                                    if count > 0:
                                        st.success(f"✅ Embedded {doc['symbol']} ({count} chunks)")
                                        time.sleep(1) 
                                        st.rerun()
                                    else:
                                        st.warning(f"⚠️ No text extracted. Scanned PDF? (Size: {len(pdf_bytes)}b)")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

                with cols[1]:
                    # CLickable Symbol
                    if doc.get('file_url'):
                        url = get_viewable_url(doc['file_url'])
                        st.markdown(f"[{doc['symbol']}]({url})")
                    else:
                        st.markdown(f"**{doc['symbol']}**")
                
                with cols[2]:
                    title_display = doc['title'][:60] + ("..." if len(doc['title']) > 60 else "")
                    st.markdown(title_display)
                with cols[3]:
                    st.markdown(get_type_badge(doc.get('doc_type')), unsafe_allow_html=True)
                with cols[4]:
                    # Session Info
                    sess = doc.get('sessions', {})
                    if sess:
                        sess_text = f"**{sess.get('group_id', '')} {sess.get('code', '')}**<br><span style='font-size:0.8em; color:gray'>{sess.get('year', '')}</span>"
                        st.markdown(sess_text, unsafe_allow_html=True)
                    else:
                        st.markdown(doc.get('author', '-'))
                with cols[5]:
                    reg_mentioned = doc.get('regulation_mentioned', '-')
                    st.markdown(f"`{reg_mentioned}`" if reg_mentioned else "-")
                with cols[6]:
                    # Actions: Just Edit and Delete
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️", key=f"edit_report_{idx}", help="Edit"):
                            st.session_state.editing_report_id = doc['id']
                            st.rerun()
                    with btn_col2:
                        if st.button("🗑️", key=f"del_report_{idx}", help="Delete"):
                            st.session_state.deleting_report_id = doc['id']
                            st.rerun()

        
        st.markdown("---")
        
        # ====================================================================
        # WORKING DOCUMENTS SECTION
        # ====================================================================
        
        if working_docs:
            # Header with Delete All button
            col_header, col_delete_all = st.columns([3, 1])
            with col_header:
                st.markdown("### 📄 Working Documents")
                st.markdown("*Formal and informal proposals*")
            with col_delete_all:
                if st.button("🗑️ Delete All Documents", type="secondary", help="Delete all documents in current view"):
                    st.session_state.confirm_delete_all = True
            
            # Delete All Confirmation
            if st.session_state.get('confirm_delete_all'):
                st.error(f"⚠️ **WARNING:** This will permanently delete ALL {len(working_docs)} documents shown below!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ YES, DELETE ALL", type="primary", use_container_width=True):
                        try:
                            client = SupabaseClient.get_client()
                            deleted_count = 0
                            failed_files = []
                            
                            for doc in working_docs:
                                # Delete PDF file from storage first if exists
                                if doc.get('file_url'):
                                    try:
                                        # Extract file path from URL
                                        # URL format: https://.../storage/v1/object/public/unece-archive/path/to/file.pdf
                                        file_path = doc['file_url'].split('/unece-archive/')[-1]
                                        client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
                                    except Exception as e:
                                        failed_files.append(f"{doc['symbol']}: {str(e)}")
                                
                                # Delete from database
                                client.table("documents").delete().eq("id", doc['id']).execute()
                                deleted_count += 1
                            
                            if failed_files:
                                st.warning(f"⚠️ Deleted {deleted_count} documents but {len(failed_files)} files couldn't be removed from storage")
                            else:
                                st.success(f"✅ Deleted {deleted_count} documents and files")
                            
                            del st.session_state.confirm_delete_all
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error during bulk deletion: {e}")
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        del st.session_state.confirm_delete_all
                        st.rerun()
                st.markdown("---")
            
            # Edit Dialog - Show BEFORE list if editing
            if st.session_state.get('editing_doc_id'):
                doc = next((d for d in working_docs if d['id'] == st.session_state.editing_doc_id), None)
                if doc:
                    st.info(f"✏️ **Editing:** {doc['symbol']}")
                    with st.form(key="edit_document_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_symbol = st.text_input("Symbol", value=doc['symbol'])
                            new_author = st.text_input("Author", value=doc['author'])
                            new_type = st.selectbox("Type", ["Report", "Agenda", "Adopted Proposals", "Formal", "Informal"], 
                                                   index=["Report", "Agenda", "Adopted Proposals", "Formal", "Informal"].index(doc['doc_type']) if doc['doc_type'] in ["Report", "Agenda", "Adopted Proposals", "Formal", "Informal"] else 0)
                        with col2:
                            new_title = st.text_area("Title", value=doc['title'], height=100)
                            
                            # Regulation Library Link (FK)
                            try:
                                all_regs = SupabaseClient.get_all_regulations()
                                reg_options = [""] + [r['id'] for r in all_regs]
                                current_ref = doc.get('regulation_ref_id') or ""
                                reg_index = reg_options.index(current_ref) if current_ref in reg_options else 0
                                new_regulation_ref = st.selectbox(
                                    "Regulation Link (from Library)", 
                                    options=reg_options,
                                    index=reg_index,
                                    help="Select regulation from library for FK link"
                                )
                            except:
                                new_regulation_ref = ""
                            
                            # Regulation Mentioned (Text)
                            new_regulation_mentioned = st.text_input(
                                "Regulation Mentioned (text)", 
                                value=doc.get('regulation_mentioned') or '',
                                help="Free text field for any mentioned regulations (e.g., 'R48, R10')"
                            )
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                        with col_cancel:
                            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                        
                        if submitted:
                            try:
                                client = SupabaseClient.get_client()
                                client.table("documents").update({
                                    "symbol": new_symbol,
                                    "title": new_title,
                                    "author": new_author,
                                    "doc_type": new_type,
                                    "regulation_ref_id": new_regulation_ref if new_regulation_ref else None,
                                    "regulation_mentioned": new_regulation_mentioned if new_regulation_mentioned else None
                                }).eq("id", doc['id']).execute()
                                st.success(f"✅ Updated {new_symbol}")
                                del st.session_state.editing_doc_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        
                        if cancelled:
                            del st.session_state.editing_doc_id
                            st.rerun()
                    st.markdown("---")
            
            # Delete Confirmation - Show BEFORE list if deleting
            if st.session_state.get('deleting_doc_id'):
                doc = next((d for d in working_docs if d['id'] == st.session_state.deleting_doc_id), None)
                if doc:
                    st.warning(f"⚠️ Delete **{doc['symbol']}**: {doc['title'][:50]}...?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True, key="confirm_delete"):
                            try:
                                client = SupabaseClient.get_client()
                                
                                # Delete PDF file from storage first if exists
                                file_deleted = False
                                file_error = None
                                if doc.get('file_url'):
                                    try:
                                        # Extract file path from URL
                                        file_path = doc['file_url'].split(f'/{Config.STORAGE_BUCKET}/')[-1]
                                        result = client.storage.from_(Config.STORAGE_BUCKET).remove([file_path])
                                        file_deleted = True
                                    except Exception as file_err:
                                        file_error = str(file_err)
                                
                                # Delete from database
                                client.table("documents").delete().eq("id", doc['id']).execute()
                                
                                # Show results
                                if file_deleted:
                                    st.success(f"✅ Deleted {doc['symbol']} (database + file)")
                                elif file_error:
                                    st.warning(f"⚠️ Deleted {doc['symbol']} (database only). File error: {file_error}")
                                else:
                                    st.success(f"✅ Deleted {doc['symbol']} (database only - no file)")
                                
                                del st.session_state.deleting_doc_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting document: {e}")
                    with col2:
                        if st.button("❌ Cancel", use_container_width=True, key="cancel_delete"):
                            del st.session_state.deleting_doc_id
                            st.rerun()
                    st.markdown("---")
            
            # Documents List with Action Buttons
            for idx, doc in enumerate(working_docs):
                # Adjusted columns: Wider Symbol (2.5), Smaller Actions (0.8)
                cols = st.columns([0.4, 2.5, 3, 0.8, 1.2, 1, 0.8])
                
                # Status Column
                with cols[0]:
                    count = embedding_counts.get(doc['id'], 0)
                    if count > 0:
                        st.markdown(f"<span style='background-color:#e6fffa; color:#047857; padding:2px 6px; border-radius:10px; font-size:0.8em; font-weight:bold;'>{count}</span>", unsafe_allow_html=True)
                    elif not doc.get('file_url'):
                        st.write(" ")
                    else:
                        if st.button("⚡", key=f"emb_doc_{idx}", help="Generate Embeddings"):
                            try:
                                with st.spinner("Wait..."):
                                    # Download file
                                    if Config.STORAGE_BUCKET in doc['file_url']:
                                        file_path = doc['file_url'].split(f'/{Config.STORAGE_BUCKET}/')[-1]
                                    else:
                                        file_path = doc['file_url']

                                    pdf_bytes = SupabaseClient.download_file(file_path)
                                    
                                    # Generate embeddings
                                    count = EmbeddingService.generate_document_embeddings(
                                        doc['id'], pdf_bytes, doc['doc_type']
                                    )
                                    
                                    if count > 0:
                                        st.success(f"✅ Embedded {doc['symbol']} ({count} chunks)")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ No text extracted. Scanned PDF?")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

                with cols[1]:
                    # Clickable Symbol
                    if doc.get('file_url'):
                        url = get_viewable_url(doc['file_url'])
                        st.markdown(f"[{doc['symbol']}]({url})")
                    else:
                        st.markdown(f"**{doc['symbol']}**")
                
                with cols[2]:
                    title_display = doc['title'][:60] + ("..." if len(doc['title']) > 60 else "")
                    st.markdown(title_display)
                with cols[3]:
                    st.markdown(get_type_badge(doc.get('doc_type')), unsafe_allow_html=True)
                with cols[4]:
                    # Session Info
                    sess = doc.get('sessions', {})
                    if sess:
                        # Re-use same formatting
                        sess_text = f"**{sess.get('group_id', '')} {sess.get('code', '')}**<br><span style='font-size:0.8em; color:gray'>{sess.get('year', '')}</span>"
                        st.markdown(sess_text, unsafe_allow_html=True)
                    else:
                        st.markdown(doc['author'])
                with cols[5]:
                    reg_mentioned = doc.get('regulation_mentioned', '-')
                    st.markdown(f"`{reg_mentioned}`" if reg_mentioned else "-")
                with cols[6]:
                    # Actions: Just Edit and Delete
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️", key=f"edit_btn_{idx}", help="Edit"):
                            st.session_state.editing_doc_id = doc['id']
                            st.rerun()
                    with btn_col2:
                        if st.button("🗑️", key=f"del_btn_{idx}", help="Delete"):
                            st.session_state.deleting_doc_id = doc['id']
                            st.rerun()


        # ============================================================================
        # PAGINATION CONTROLS
        # ============================================================================
        st.markdown("---")
        if total_items > 0:
            pg_col1, pg_col2, pg_col3 = st.columns([1, 2, 1])
            
            with pg_col1:
                if st.session_state.current_page > 1:
                    if st.button("⬅️ Previous Page"):
                        st.session_state.current_page -= 1
                        st.rerun()
            
            with pg_col2:
                st.markdown(f"<div style='text-align: center'>Page <b>{st.session_state.current_page}</b> of <b>{total_pages}</b></div>", unsafe_allow_html=True)
                
            with pg_col3:
                if st.session_state.current_page < total_pages:
                    if st.button("Next Page ➡️"):
                        st.session_state.current_page += 1
                        st.rerun()

except Exception as e:
    st.error(f"Error loading documents: {e}")
    st.exception(e)


