import streamlit as st
import pandas as pd
from supabase_client import SupabaseClient
from extract_proposals import ProposalExtractor
from config import Config
import time
import re

st.set_page_config(page_title="Adopted Proposals", page_icon="📜", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("📜 Adopted Proposals Dashboard")

# Navigation Logic with Redirect Handling
if 'page_nav' not in st.session_state:
    st.session_state['page_nav'] = "🚀 Scan & Ingest"

# Check for redirect from previous run
if 'redirect_to' in st.session_state and st.session_state['redirect_to']:
    st.session_state['page_nav'] = st.session_state['redirect_to']
    del st.session_state['redirect_to']

# 2. Tab Replacement
page = st.radio("Navigation", ["🚀 Scan & Ingest", "📊 Dashboard"], key="page_nav", horizontal=True, label_visibility="collapsed")

# Helper for Regulation Sorting
def reg_sort_key(reg_id):
    """Sort regulations numerically: R9 < R13 < R109"""
    match = re.search(r'R(\d+)', str(reg_id), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 999999

# ==============================================================================
# VIEW 1: SCAN & INGEST
# ==============================================================================
if page == "🚀 Scan & Ingest":
    st.markdown("### Scan New Proposals")
    st.markdown("Select a session document (Report or Adopted Proposal) to extract regulation updates.")
    
    # 1. Select Session
    try:
        # Get WP29 sessions first (most likely)
        groups = SupabaseClient.get_all_groups()
        wp29_id = next((g['id'] for g in groups if g['id'] in ['WP29', 'WP.29']), None)
        
        all_sessions = []
        if wp29_id:
             all_sessions = SupabaseClient.get_sessions_by_group(wp29_id)
        
        # Sort by year desc
        all_sessions.sort(key=lambda x: x['year'], reverse=True)
        
        session_opts = {s['id']: f"{s['code']} ({s['year']})" for s in all_sessions}
        
        sel_session_id = st.selectbox(
            "Select WP.29 Session",
            options=session_opts.keys(),
            format_func=lambda x: session_opts[x]
        )
        
        if sel_session_id:
            # 2. Select Document
            docs = SupabaseClient.get_documents_by_session(sel_session_id)
            # Filter for likely candidates
            relevant_docs = [d for d in docs if d['doc_type'] in ['Report', 'Adopted Proposals', 'Agenda']]
            
            if not relevant_docs:
                st.warning("No reports or adopted proposals found for this session.")
            else:
                doc_opts = {d['id']: f"{d['symbol']} - {d['title'][:50]}..." for d in relevant_docs}
                sel_doc_id = st.selectbox(
                    "Select Document to Scan",
                    options=doc_opts.keys(),
                    format_func=lambda x: doc_opts[x]
                )
                
                # Check duplication
                client = SupabaseClient.get_client()
                try:
                    res = client.table("adopted_proposals").select("id", count="exact", head=True).eq("source_doc_id", sel_doc_id).execute()
                    count = res.count
                except Exception:
                    count = 0
                
                if count and count > 0:
                    st.success(f"✅ Protocol already scanned ({count} proposals extracted).")
                    st.caption("To re-scan, you must delete the existing entries in the dashboard.")
                else:
                    # SCAN BUTTON
                    if st.button("🚀 Scan Document", type="primary"):
                        with st.spinner("Analyzing document with Gemini... (this may take 30s)"):
                            try:
                                extracted_data = ProposalExtractor.extract_proposals_from_doc(sel_doc_id)
                                if extracted_data:
                                    st.session_state['staging_proposals'] = extracted_data
                                    st.session_state['staging_doc_id'] = sel_doc_id
                                    st.session_state['staging_session_id'] = sel_session_id
                                    st.success(f"Extracted {len(extracted_data)} proposals!")
                                else:
                                    st.warning("No proposals found or extraction failed.")
                            except Exception as e:
                                st.error(f"Error during extraction: {e}")

    except Exception as e:
        st.error(f"Error loading sessions: {e}")

    # STAGING AREA
    if 'staging_proposals' in st.session_state and st.session_state['staging_proposals']:
        st.markdown("---")
        st.subheader("📝 Review & Edit Results")
        
        # Display Context
        if session_opts and 'staging_session_id' in st.session_state:
            ctx_session = session_opts.get(st.session_state['staging_session_id'], "Unknown Session")
            st.info(f"Target Session: **{ctx_session}**")
            st.caption("Please review the extracted data. Edit descriptions or details if needed. Click 'Save' to finalize.")
        
        # Convert to DataFrame for Editor
        df = pd.DataFrame(st.session_state['staging_proposals'])
        
        # Ensure regex columns exist
        required_cols = ["regulation_id", "series", "supplement", "entry_date", "description", "status", "document_code"]
        for c in required_cols:
            if c not in df.columns:
                df[c] = None

        # Fix Data Types for Editor
        if "entry_date" in df.columns:
            df["entry_date"] = pd.to_datetime(df["entry_date"], errors='coerce')
                
        # Configure columns
        column_config = {
            "regulation_id": st.column_config.TextColumn("Regulation", help="e.g. R48"),
            "series": st.column_config.TextColumn("Series", help="09"),
            "supplement": st.column_config.TextColumn("Suppl.", help="12"),
            "entry_date": st.column_config.DateColumn("Entry Date", format="YYYY-MM-DD"),
            "description": st.column_config.TextColumn("Description", width="large", required=True),
            "status": st.column_config.SelectboxColumn("Status", options=["Adopted", "Entered into Force", "Frozen"]),
            "document_code": st.column_config.TextColumn("Doc Ref", help="e.g. 2025/67")
        }
        
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="staging_editor"
        )
        
        # Check constraints
        missing_desc = edited_df[edited_df['description'].isna() | (edited_df['description'] == "")]
        if not missing_desc.empty:
            st.warning(f"⚠️ {len(missing_desc)} rows are missing a description. Please fill them in.")
        
        # SAVE BUTTON
        if st.button("💾 Save Verified Proposals", type="primary", disabled=not missing_desc.empty):
            # Prepare data for insert
            records = edited_df.to_dict('records')
            doc_id = st.session_state['staging_doc_id']
            sess_id = st.session_state['staging_session_id']
            
            clean_records = []
            for r in records:
                # Handle Date conversion safely
                e_date = r.get("entry_date")
                if pd.isna(e_date):
                    final_date = None
                else:
                    try:
                        final_date = e_date.strftime('%Y-%m-%d')
                    except:
                        final_date = None

                clean_records.append({
                    "regulation_id": r.get("regulation_id"),
                    "series": r.get("series"),
                    "supplement": r.get("supplement"),
                    "entry_date": final_date,
                    "description": r.get("description"),
                    "status": r.get("status", "Adopted"),
                    "document_code": r.get("document_code"),
                    "source_doc_id": doc_id,
                    "session_id": sess_id
                })
            
            # Insert
            try:
                # Use Admin Client for all write ops
                client = SupabaseClient.get_admin_client()
                
                # 1. Ensure Regulations Exist (Fix: Foreign Key Violation)
                unique_regs = list(set([r['regulation_id'] for r in clean_records if r['regulation_id']]))
                
                if unique_regs:
                    existing = client.table("regulations").select("id").in_("id", unique_regs).execute()
                    existing_ids = {item['id'] for item in existing.data}
                    
                    missing_regs = [rid for rid in unique_regs if rid not in existing_ids]
                    
                    if missing_regs:
                        # Auto-create missing regulations
                        new_reg_data = [{"id": rid, "title": f"Regulation {rid}", "topic": "Unknown - Auto-created"} for rid in missing_regs]
                        client.table("regulations").insert(new_reg_data).execute()
                        st.toast(f"✅ Auto-created {len(missing_regs)} missing regulations in library.")
                
                # 2. Insert Proposals
                res = client.table("adopted_proposals").insert(clean_records).execute()
                st.success(f"✅ Successfully saved {len(clean_records)} proposals!")
                # Clear staging
                del st.session_state['staging_proposals']
                del st.session_state['staging_doc_id']
                del st.session_state['staging_session_id']
                # Navigate to Dashboard
                st.session_state['redirect_to'] = "📊 Dashboard"
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error saving to database: {e}")
                st.caption("Ensure you have run the `init_adopted_proposals.sql` script in Supabase.")


# ==============================================================================
# VIEW 2: DASHBOARD
# ==============================================================================
elif page == "📊 Dashboard":
    st.markdown("### 📚 Adopted Proposals Library")
    
    try:
        client = SupabaseClient.get_client()
        res = client.table("adopted_proposals").select("*, sessions(code, year)").order("created_at", desc=True).limit(500).execute()
        
        data = res.data
        if not data:
            st.info("No proposals found. Go to 'Scan' tab.")
        else:
            # Flatten session info
            flat_data = []
            for item in data:
                s = item.get('sessions') or {}
                item['session_label'] = f"WP.29 {s.get('code','?')} ({s.get('year','?')})"
                flat_data.append(item)
            
            df_dash = pd.DataFrame(flat_data)
            
            # 1. Regulation Filter (Sorted Numeric)
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                raw_regs = list(set(df_dash['regulation_id'].dropna()))
                # Use custom sort key
                all_regs = sorted(raw_regs, key=reg_sort_key)
                sel_regs = st.multiselect("Filter Regulation", all_regs)
            
            with col_filter2:
                # Session Filter
                all_sessions = sorted(list(set(df_dash['session_label'].dropna())))
                sel_sessions = st.multiselect("Filter Session", all_sessions)

            # Advanced Filters Expander (Opened if any active)
            # We don't want to force it open/closed on re-run unless we track state, but standard expander is fine.
            with st.expander("🔍 More Filters (Description, Series, Status)"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    search_desc = st.text_input("Search Description", placeholder="e.g. Braking...")
                with c2:
                    all_status = sorted(list(set(df_dash['status'].dropna())))
                    sel_status = st.multiselect("Filter Status", all_status)
                with c3:
                    all_series = sorted(list(set(df_dash['series'].dropna())))
                    sel_series = st.multiselect("Filter Series", all_series)
            
            # Sorting (User Request)
            col_sort1, col_sort2 = st.columns(2)
            with col_sort1:
                sort_col = st.selectbox("Sort By", ["Created At (Default)", "Regulation", "Series", "Entry Date", "Status", "Session"])
            with col_sort2:
                sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, label_visibility="collapsed")

            # Apply Filters
            if sel_regs:
                df_dash = df_dash[df_dash['regulation_id'].isin(sel_regs)]
            if sel_sessions:
                df_dash = df_dash[df_dash['session_label'].isin(sel_sessions)]
            if search_desc:
                df_dash = df_dash[df_dash['description'].str.contains(search_desc, case=False, na=False)]
            if sel_status:
                df_dash = df_dash[df_dash['status'].isin(sel_status)]
            if sel_series:
                df_dash = df_dash[df_dash['series'].isin(sel_series)]
            
            # Apply Sorting
            ascending = True if sort_order == "Ascending" else False
            if sort_col == "Regulation":
                # Use custom sort key logic if possible, or just standard sort
                # Since 'reg_num' logic is below in group view, let's replicate simplistic version or just string sort
                # For robust reg sort we need the extraction again
                df_dash['reg_num'] = df_dash['regulation_id'].apply(reg_sort_key)
                df_dash = df_dash.sort_values('reg_num', ascending=ascending)
            elif sort_col == "Series":
                df_dash = df_dash.sort_values('series', ascending=ascending, na_position='last')
            elif sort_col == "Entry Date":
                df_dash = df_dash.sort_values('entry_date', ascending=ascending, na_position='last')
            elif sort_col == "Status":
                df_dash = df_dash.sort_values('status', ascending=ascending)
            elif sort_col == "Session":
                df_dash = df_dash.sort_values('session_label', ascending=ascending)
            else:
                # Default Created At
                df_dash = df_dash.sort_values('created_at', ascending=ascending)
            
            # View Mode
            view_mode = st.radio("View", ["Table", "Grouped"], horizontal=True)
            
            if view_mode == "Table":
                st.caption("You can edit descriptions directly here (click Save Changes to persist).")
                
                # Configure grid
                edited_dash = st.data_editor(
                    df_dash,
                    column_config={
                        "id": None, # Hide ID
                        "source_doc_id": None,
                        "session_id": None,
                        "created_at": None,
                        "updated_at": None,
                        "sessions": None,
                        "regulation_id": st.column_config.TextColumn("Reg", width="small", help="Regulation ID"),
                        "series": st.column_config.TextColumn("Series", width="small"),
                        "supplement": st.column_config.TextColumn("Suppl.", width="small"),
                        "entry_date": st.column_config.TextColumn("Entry Date", width="medium"),
                        "description": st.column_config.TextColumn("Description", width="large"),
                        "session_label": st.column_config.TextColumn("Session", width="medium", disabled=True),
                        "status": st.column_config.TextColumn("Status", width="small"),
                        "document_code": st.column_config.TextColumn("Doc Ref", width="small")
                    },
                    use_container_width=True,
                    num_rows="dynamic",
                    hide_index=True,
                    key="dash_editor"
                )
                
                if st.button("💾 Save Changes (Dashboard)"):
                    try:
                        # Use Admin Client for updates
                        client = SupabaseClient.get_admin_client()
                        
                        to_upsert = []
                        # Iterate rows from editor
                        for index, row in edited_dash.iterrows():
                            # We only care about rows with an ID (updates)
                            if row.get('id'):
                                to_upsert.append({
                                    "id": row['id'],
                                    "description": row['description'],
                                    "series": row['series'],
                                    "supplement": row['supplement'],
                                    "entry_date": row['entry_date'],
                                    "status": row['status'],
                                    "document_code": row.get('document_code')
                                })
                        
                        if to_upsert:
                            # Use upsert in batches? 
                            # Supabase-py allows list upsert
                            client.table("adopted_proposals").upsert(to_upsert).execute()
                            st.success(f"Saved {len(to_upsert)} rows!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.info("No rows to save.")
                            
                    except Exception as e:
                        st.error(f"Error saving: {str(e)}")
                            
            else:
                # Grouped View (Sorted by Reg Number)
                df_dash['reg_num'] = df_dash['regulation_id'].apply(reg_sort_key)
                df_dash = df_dash.sort_values('reg_num')
                
                grouped = df_dash.groupby("regulation_id", sort=False) # Already sorted
                
                for reg, group in grouped:
                    with st.expander(f"**{reg}** ({len(group)} updates)"):
                        # Sort group by date desc
                        group = group.sort_values('created_at', ascending=False)
                        for i, row in group.iterrows():
                            st.markdown(f"**{row['session_label']}** - {row['status']}")
                            st.markdown(f"**Series**: {row['series']} | **Suppl**: {row['supplement']} | **Date**: {row['entry_date']}")
                            st.info(row['description'])
                            st.divider()

    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
             st.error("Table `adopted_proposals` not found. Please ask Admin to run `init_adopted_proposals.sql`.")
        else:
             st.error(f"Error loading dashboard: {e}")
