import streamlit as st
from supabase_client import SupabaseClient
from config import Config
import pandas as pd
from datetime import datetime
import time
from embedding_service import EmbeddingService

st.set_page_config(page_title="Interpretations Library", page_icon="📖", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("📖 Interpretations Library")
st.markdown("Browse and search official interpretations from Ministries, TAAM, and Internal sources.")

# --- Side Bar Filters ---
with st.sidebar:
    st.header("Filters")
    
    # Text Search
    search_term = st.text_input("🔍 Search", placeholder="Title, Reg, or Content...")
    
    # Fetch Data first to populate filters
    # Note: Optimization would be to fetch unique values separately or cache the full data
    try:
        # We assume RLS handles what we can see. 
        # For authenticated 'advanced' users, they should see private too.
        # But we don't have auth state yet in session properly, assuming public/anon allowed by fix script.
        # Ideally we'd toggle include_private based on actual user role.
        # For now, fetch ALL available to current session.
        all_interps = SupabaseClient.get_interpretations(include_private=True)
    except Exception as e:
        st.error(f"Error loading interpretations: {e}")
        all_interps = []

    if not all_interps:
        st.warning("No interpretations found.")
        st.stop()
        
    df = pd.DataFrame(all_interps)
    
    # Normalize Issuer Data (flattens json)
    if not df.empty and 'issuers' in df.columns:
        df['issuer_name'] = df['issuers'].apply(lambda x: x.get('name') if x else 'Unknown')
        df['issuer_code'] = df['issuers'].apply(lambda x: x.get('code') if x else 'Unknown')
    else:
        df['issuer_name'] = 'Unknown'
        df['issuer_code'] = 'UNK'

    # Filter: Issuer
    all_issuers = sorted(df['issuer_name'].unique().tolist())
    selected_issuers = st.multiselect("Issuer", all_issuers, default=[])
    
    # Filter: Status
    all_statuses = sorted(df['status'].unique().tolist())
    selected_statuses = st.multiselect("Status", all_statuses, default=[])

    # Filter: Regulation
    # Extract regs, they might be free text. Simple text filter or unique values if structured.
    # User input reg_ref is text.
    
    # Toggle: Show Public/Private
    # show_private = st.checkbox("Show Private", value=True) # RLS handles this actually

# --- Filtering Logic ---
filtered_df = df.copy()

if search_term:
    # Case insensitive search across multiple fields
    term = search_term.lower()
    mask = (
        filtered_df['title'].str.lower().str.contains(term, na=False) |
        filtered_df['regulation_mentioned'].str.lower().str.contains(term, na=False) |
        filtered_df['comments'].str.lower().str.contains(term, na=False) |
        filtered_df['content_text'].str.lower().str.contains(term, na=False)
    )
    filtered_df = filtered_df[mask]

if selected_issuers:
    filtered_df = filtered_df[filtered_df['issuer_name'].isin(selected_issuers)]

if selected_statuses:
    filtered_df = filtered_df[filtered_df['status'].isin(selected_statuses)]

# --- Display Results ---
# --- Display Results ---
st.markdown(f"**Found {len(filtered_df)} documents**")

# Check Embedding Status
embedded_counts = {}
if not filtered_df.empty:
    try:
        # Get IDs of displayed interpretations
        interp_ids = filtered_df['id'].tolist()
        
        # Batch query to check which ones have embeddings
        client = SupabaseClient.get_client()
        
        # Split into chunks if too many
        chunk_size = 20
        for i in range(0, len(interp_ids), chunk_size):
            batch = interp_ids[i:i + chunk_size]
            res = client.table("embeddings").select("source_id").in_("source_id", batch).eq("source_type", "interpretation").execute()
            
            # Count chunks per document
            for item in res.data:
                sid = item['source_id']
                embedded_counts[sid] = embedded_counts.get(sid, 0) + 1
            
    except Exception as e:
        st.error(f"Error checking status: {e}")

# Pre-fetch ALL issuers for the edit dropdown
try:
    all_issuers_data = SupabaseClient.get_all_issuers()
# ... (rest of code)

    # Create map {id: name} and list of names
    issuer_options = {i['id']: f"{i['name']} ({i['code']})" for i in all_issuers_data}
except:
    issuer_options = {}

for index, row in filtered_df.iterrows():
    with st.container():
        
        # Unique key for this item's edit mode
        edit_key = f"edit_mode_{row['id']}"
        
        # --- VIEW MODE ---
        if not st.session_state.get(edit_key, False):
            # Card Header
            col1, col2 = st.columns([4, 1])
            with col1:
                # Status Icon & Count
                chunks = embedded_counts.get(row['id'], 0)
                is_embedded = chunks > 0
                status_icon = "🟢" if is_embedded else "⚡"
                count_badge = f" `({chunks} chunks)`" if is_embedded else ""
                
                vis_icon = "🔒" if not row.get('is_public') else "🌍"
                title_text = f"#### {status_icon} {vis_icon} {row['title']}{count_badge}"
                st.markdown(title_text)
                st.caption(f"**{row['issuer_name']}** ({row['issuer_code']}) | Date: {row['issue_date']} | Status: `{row['status']}`")
                
                # Show Embed Option if missing and user has file
                if not is_embedded and row.get('file_url'):
                    if st.button(f"🚀 Generate Embeddings", key=f"btn_emb_{row['id']}"):
                        try:
                            with st.spinner("Embedding..."):
                                # 1. Download File
                                path = row['file_url'].split(f'/{Config.STORAGE_BUCKET}/')[-1]
                                pdf_data = SupabaseClient.download_file(path)
                                
                                # 2. Generate
                                count, err = EmbeddingService.generate_interpretation_embeddings(
                                    interpretation_id=row['id'],
                                    pdf_bytes=pdf_data
                                )
                                
                                if count > 0:
                                    st.success(f"Generated {count} chunks!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {err}")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col2:
                # Action Buttons
                if row.get('file_url'):
                    full_url = SupabaseClient.get_public_url(row['file_url'])
                    st.link_button("📄 Open PDF", full_url)
                
                # Edit Button
                if st.button("✏️ Edit", key=f"btn_edit_{row['id']}"):
                    st.session_state[edit_key] = True
                    st.rerun()

            # Card Body
            if row.get('regulation_mentioned'):
                st.markdown(f"**Regulation:** {row['regulation_mentioned']}")
            
            if row.get('comments'):
                st.info(row['comments'])

        # --- EDIT MODE ---
        else:
            with st.form(key=f"form_edit_{row['id']}"):
                st.subheader(f"Editing: {row['title']}")
                
                new_title = st.text_input("Title", value=row['title'])
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    # Date input requires conversion to date object
                    try:
                        default_date = datetime.strptime(row['issue_date'], '%Y-%m-%d').date()
                    except:
                        default_date = datetime.today().date()
                    new_date = st.date_input("Issue Date", value=default_date)
                
                with c2:
                    current_issuer_id = row['issuer_id']
                    # Find index
                    keys = list(issuer_options.keys())
                    formatted_names = list(issuer_options.values())
                    try:
                        default_idx = keys.index(current_issuer_id)
                    except:
                        default_idx = 0
                    
                    selected_issuer_idx = st.selectbox("Issuer", range(len(formatted_names)), format_func=lambda x: formatted_names[x], index=default_idx)
                    new_issuer_id = keys[selected_issuer_idx] if keys else current_issuer_id

                with c3:
                    status_opts = ['draft', 'final', 'superseded']
                    try:
                        s_idx = status_opts.index(row['status'])
                    except:
                        s_idx = 0
                    new_status = st.selectbox("Status", status_opts, index=s_idx)
                
                new_reg = st.text_input("Regulation Mentioned", value=row['regulation_mentioned'] or "")
                new_comments = st.text_area("Comments", value=row['comments'] or "")
                
                new_is_public = st.checkbox("Public Visibility (🌍)", value=row['is_public'])
                
                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.form_submit_button("💾 Save Changes"):
                        try:
                            # Update DB
                            SupabaseClient.update_interpretation(
                                interp_id=row['id'],
                                title=new_title,
                                issuer_id=new_issuer_id,
                                issue_date=new_date.strftime('%Y-%m-%d'),
                                status=new_status,
                                regulation_mentioned=new_reg,
                                comments=new_comments,
                                is_public=new_is_public
                            )
                            st.success("Updated!")
                            st.session_state[edit_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating: {e}")
                
                with b2:
                    # Separation for layout
                    pass
            
            # Additional Actions: Delete
            st.markdown("### Danger Zone")
            c_del1, c_del2 = st.columns([1, 4])
            with c_del1:
                if st.button("🗑️ Delete", key=f"btn_del_{row['id']}", type="primary"):
                    st.session_state[f"confirm_del_{row['id']}"] = True
                    st.rerun()
            
            with c_del2:
                if st.session_state.get(f"confirm_del_{row['id']}"):
                    st.warning("Are you sure? This cannot be undone.")
                    cd1, cd2 = st.columns(2)
                    with cd1:
                        if st.button("Yes, Delete", key=f"btn_yes_del_{row['id']}"):
                            SupabaseClient.delete_interpretation(row['id'])
                            st.success("Deleted.")
                            st.session_state[f"confirm_del_{row['id']}"] = False
                            st.session_state[edit_key] = False
                            st.rerun()
                    with cd2:
                        if st.button("No, Cancel", key=f"btn_no_del_{row['id']}"):
                            st.session_state[f"confirm_del_{row['id']}"] = False
                            st.rerun()

            st.markdown("---")
            # Cancel Button (Return to view)
            if st.button("🔙 Back to View", key=f"btn_cancel_{row['id']}"):
                st.session_state[edit_key] = False
                st.rerun()

        st.markdown("---")
