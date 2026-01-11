"""
Page 9: My Meetings
Display all sessions organized hierarchically with document counts
"""
import streamlit as st
from supabase_client import SupabaseClient
import pandas as pd

st.set_page_config(page_title="My Meetings", page_icon="📅", layout="wide")

from auth_utils import require_auth
require_auth()

st.title("📅 My Meetings")
st.markdown("Browse all sessions organized by working group hierarchy")

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data(ttl=300)
def load_sessions_with_counts():
    """Load all sessions with document counts, grouped by type"""
    try:
        client = SupabaseClient.get_client()
        
        # Get all sessions
        sessions_resp = client.table("sessions").select("*").execute()
        if not sessions_resp.data:
            return []
        
        # Get all working groups
        groups_resp = client.table("groups").select("*").execute()
        groups = {g['id']: g for g in groups_resp.data} if groups_resp.data else {}
        
        # Build sessions with counts
        sessions_with_counts = []
        for session in sessions_resp.data:
            # Get group info - in groups table, 'id' is the code (GRE, WP.29, etc.)
            group = groups.get(session['group_id'], {})
            parent_id = group.get('parent_group_id')
            parent_group = groups.get(parent_id, {}) if parent_id else {}
            
            # Count documents for this session
            doc_count_resp = client.table("documents").select("id", count="exact").eq("session_id", session['id']).execute()
            doc_count = doc_count_resp.count if doc_count_resp.count else 0
            
            sessions_with_counts.append({
                'session_id': session['id'],
                'session_code': session['code'],
                'year': session['year'],
                'group_code': group.get('id', 'Unknown'),  # id IS the code
                'group_name': group.get('full_name', 'Unknown'),
                'group_type': group.get('type', 'Unknown'),  # GR, TF, IWG, etc.
                'parent_id': parent_id,
                'parent_code': parent_group.get('id'),  # id IS the code
                'doc_count': doc_count
            })
        
        return sessions_with_counts
    except Exception as e:
        st.error(f"Error loading sessions: {e}")
        return []

# Load data
try:
    with st.spinner("Loading sessions..."):
        sessions = load_sessions_with_counts()

    if not sessions:
        st.info("No sessions found. Create sessions in the Admin Structure page.")
        st.stop()
except Exception as e:
    st.error(f"Error loading page: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# ============================================================================
# ORGANIZE BY HIERARCHY
# ============================================================================

# Group sessions by type
wp29_sessions = []
gr_sessions = []
tf_iwg_sessions = []

for s in sessions:
    # WP.29 can be stored as "WP.29" or "WP29" in the database
    if s['group_code'] in ['WP.29', 'WP29']:
        wp29_sessions.append(s)
    elif s['group_type'] == 'GR':
        # GR - Working Groups (regardless of parent)
        gr_sessions.append(s)
    else:
        # TF/IWG - Task Forces and Informal Working Groups
        tf_iwg_sessions.append(s)

# Sort sessions within each group (newest first)
# Sort sessions within each group (newest first)
def sort_sessions(sess_list):
    # Sort key: 
    # 1. Year (descending)
    # 2. Type Priority (0 for numeric codes, 1 for string codes)
    # 3. Numeric Value (descending) OR String Value (ascending)
    def sort_key(x):
        code = str(x['session_code'])
        if code.isdigit():
            # Priority 0: Numeric sessions (descending)
            return (-x['year'], 0, -int(code))
        else:
            # Priority 1: String sessions (like "Literature")
            return (-x['year'], 1, code)
            
    return sorted(sess_list, key=sort_key)

wp29_sessions = sort_sessions(wp29_sessions)
gr_sessions = sort_sessions(gr_sessions)
tf_iwg_sessions = sort_sessions(tf_iwg_sessions)

# ============================================================================
# DISPLAY
# ============================================================================

# Helper to render grouped sections
def render_grouped_section(title, sessions_list, expanded=False):
    st.markdown(f"### {title}")
    
    if not sessions_list:
        st.caption("No sessions found")
        return

    # Group by group_code
    grouped = {}
    for s in sessions_list:
        code = s['group_code']
        if code not in grouped:
            grouped[code] = []
        grouped[code].append(s)
        
    # Sort groups alphabetically
    sorted_groups = sorted(grouped.keys())
    
    for g_code in sorted_groups:
        group_sessions = grouped[g_code]
        # Calculate total docs for group
        total_group_docs = sum(s['doc_count'] for s in group_sessions)
        
        # Expander for the Group (TF/GR)
        with st.expander(f"**{g_code}** ({len(group_sessions)} sessions, {total_group_docs} docs)", expanded=False):
            for s in group_sessions:
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Determine display name based on context
                    if s['session_code'] == 'Literature':
                         display_name = f"{s['group_code']} - Literature Materials"
                    else:
                         display_name = f"{s['group_code']} - Session {s['session_code']} ({s['year']})"
                    
                    if s['doc_count'] > 0:
                        display_name += f" - **{s['doc_count']} docs**"
                    else:
                        display_name += f" - {s['doc_count']} docs"

                    if st.button(
                        display_name,
                        key=f"btn_{s['session_id']}",
                        use_container_width=True
                    ):
                        st.session_state['filter_group_main'] = s['group_code']
                        st.session_state['filter_session_main'] = s['session_code']
                        st.session_state['filter_year_main'] = str(s['year'])
                        st.switch_page("pages/4_Search_Session.py")

# WP.29 Sessions (Keep as is or group? WP29 is usually just one group)
with st.expander("🏛️ **WP.29**", expanded=True):
    if wp29_sessions:
        for s in wp29_sessions:
             col1, col2 = st.columns([4, 1])
             with col1:
                display_name = f"WP.29 - {s['session_code']} ({s['year']}) - **{s['doc_count']} docs**"
                if st.button(display_name, key=f"wp29_{s['session_id']}", use_container_width=True):
                    st.session_state['filter_group_main'] = s['group_code']
                    st.session_state['filter_session_main'] = s['session_code']
                    st.session_state['filter_year_main'] = str(s['year'])
                    st.switch_page("pages/4_Search_Session.py")
    else:
        st.caption("No WP.29 sessions found")

# GR Sessions - Grouped
render_grouped_section("📊 GR - Working Groups", gr_sessions)

# TF/IWG Sessions - Grouped
render_grouped_section("🔬 TF / IWG", tf_iwg_sessions)

# Summary statistics
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Sessions", len(sessions))
with col2:
    st.metric("WP.29 Sessions", len(wp29_sessions))
with col3:
    st.metric("GR Sessions", len(gr_sessions))
with col4:
    st.metric("TF/IWG Sessions", len(tf_iwg_sessions))

total_docs = sum(s['doc_count'] for s in sessions)
st.metric("Total Documents", total_docs)
