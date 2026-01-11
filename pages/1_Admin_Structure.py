"""
Page 1: Admin & Structure
Group and Session Management
"""
import streamlit as st
from supabase_client import SupabaseClient
import pandas as pd

st.set_page_config(page_title="Admin & Structure", page_icon="🏛️", layout="wide")

from auth_utils import require_auth, check_permission
require_auth()

if not check_permission('collaborator'):
    st.error("⛔ Access Denied: You need at least 'Collaborator' privileges to view this page.")
    st.image("https://media.giphy.com/media/njYrp176NnVIn3rfkp/giphy.gif")
    st.stop()

st.title("🏛️ Admin & Structure")
st.markdown("Manage groups (WP29, GRs, IWGs) and sessions")

# Bootstrap: Create WP29 if database is empty
def bootstrap_database():
    """Create WP29 root group if database is empty"""
    try:
        groups = SupabaseClient.get_all_groups()
        if not groups:
            SupabaseClient.create_group(
                group_id="WP29",
                full_name="World Forum for Harmonization of Vehicle Regulations",
                group_type="WP",
                parent_id=None
            )
            st.success("✅ Created WP29 root group")
            return True
    except Exception as e:
        st.error(f"Error bootstrapping database: {e}")
    return False

# Run bootstrap check
if 'bootstrapped' not in st.session_state:
    bootstrap_database()
    st.session_state.bootstrapped = True

# Tabs
tab1, tab2 = st.tabs(["📁 Groups", "📅 Sessions"])

# Helper: Sort groups (WP29 -> GRs -> TF/IWGs)
def get_group_sort_key(g):
    # Priority 0: WP29
    if g['id'].upper() == 'WP29':
        return (0, g['id'])
    # Priority 1: GRs
    if g['type'] == 'GR':
        return (1, g['id'])
    # Priority 2: everything else (TF, IWG, etc.)
    return (2, g['id'])

# ============================================================================
# TAB 1: GROUP MANAGEMENT
# ============================================================================

with tab1:
    st.markdown("### Group Hierarchy")
    
    try:
        # Fetch all groups
        groups = SupabaseClient.get_all_groups()
        
        if groups:
            # Display as tree
            st.markdown("#### Current Structure")
            
            # Build tree structure
            group_dict = {g['id']: g for g in groups}
            root_groups = [g for g in groups if g['parent_group_id'] is None]
            
            # SORT ROOTS
            root_groups.sort(key=get_group_sort_key)
            
            def display_tree(group, level=0):
                # Use non-breaking spaces for visible indentation in Streamlit
                # level 0: ""
                # level 1: "&nbsp;&nbsp;&nbsp;&nbsp;↳ "
                # level 2: "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ "
                if level == 0:
                    indent_str = ""
                    prefix = ""
                else:
                    indent_str = "&nbsp;&nbsp;&nbsp;&nbsp;" * level
                    prefix = "↳ "
                
                icon = "📁" if group['type'] in ['WP', 'GR'] else "📂"
                
                # Render using HTML to ensure spaces are respected
                st.markdown(f"{indent_str}{prefix}{icon} **{group['id']}** - {group['full_name']} ({group['type']})", unsafe_allow_html=True)
                
                # Find children
                children = [g for g in groups if g.get('parent_group_id') == group['id']]
                
                # SORT CHILDREN
                children.sort(key=get_group_sort_key)
                
                for child in children:
                    display_tree(child, level + 1)
            
            for root in root_groups:
                display_tree(root)
        else:
            st.info("No groups found. Add your first group below.")
    
    except Exception as e:
        st.error(f"Error loading groups: {e}")
    
    st.markdown("---")
    st.markdown("### ➕ Add New Group")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_group_id = st.text_input("Group ID", placeholder="e.g., GRE, GRVA, IWG-SLR")
        new_group_name = st.text_input("Full Name", placeholder="e.g., Working Party on Lighting")
        new_group_type = st.selectbox("Type", ["GR", "IWG", "TF", "Committee"])
    
    with col2:
        # Get parent options
        try:
            # Sort parent options too for nicer UX
            all_groups_sorted = sorted(SupabaseClient.get_all_groups(), key=get_group_sort_key)
            parent_options = ["None (Root)"] + [g['id'] for g in all_groups_sorted]
            selected_parent = st.selectbox("Parent Group", parent_options)
            parent_id = None if selected_parent == "None (Root)" else selected_parent
        except:
            parent_id = None
        
        st.markdown("")
        st.markdown("")
        
        if st.button("➕ Create Group", type="primary", use_container_width=True):
            if new_group_id and new_group_name:
                try:
                    SupabaseClient.create_group(
                        group_id=new_group_id,
                        full_name=new_group_name,
                        group_type=new_group_type,
                        parent_id=parent_id
                    )
                    st.success(f"✅ Created group: {new_group_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating group: {e}")
            else:
                st.warning("Please fill in all required fields")

# ============================================================================
# TAB 2: SESSION MANAGEMENT
# ============================================================================

with tab2:
    st.markdown("### Session Management")
    
    # Group selector
    try:
        groups = SupabaseClient.get_all_groups()
        if not groups:
            st.warning("Please create a group first")
        else:
            # SORT GROUPS FOR DROPDOWN
            groups.sort(key=get_group_sort_key)
            
            selected_group = st.selectbox(
                "Select Group",
                options=[g['id'] for g in groups],
                format_func=lambda x: f"{x} - {next(g['full_name'] for g in groups if g['id'] == x)}"
            )
            
            if selected_group:
                st.markdown(f"#### Sessions for **{selected_group}**")
                
                # Display existing sessions
                sessions = SupabaseClient.get_sessions_by_group(selected_group)
                
                if sessions:
                    # Create dataframe for display
                    df = pd.DataFrame(sessions)
                    df = df[['code', 'year', 'dates', 'id']].sort_values('year', ascending=False)
                    df.columns = ['Session Code', 'Year', 'Dates', 'ID']
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No sessions found for this group")
                
                st.markdown("---")
                st.markdown("### ➕ Create New Session")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    session_code = st.text_input("Session Code", placeholder="e.g., 90")
                
                with col2:
                    session_year = st.number_input("Year", min_value=2000, max_value=2100, value=2024)
                
                with col3:
                    session_dates = st.text_input("Dates (optional)", placeholder="e.g., 5-8 March 2024")
                
                if st.button("➕ Create Session", type="primary"):
                    if session_code:
                        try:
                            SupabaseClient.create_session(
                                group_id=selected_group,
                                code=session_code,
                                year=session_year,
                                dates=session_dates if session_dates else None
                            )
                            st.success(f"✅ Created session: {selected_group} Session {session_code}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating session: {e}")
                    else:
                        st.warning("Please enter a session code")
                
                # Edit Existing Session
                st.markdown("---")
                with st.expander("✏️ Edit Existing Session"):
                    if sessions:
                        session_to_edit = st.selectbox(
                            "Select Session to Edit",
                            options=sessions,
                            format_func=lambda x: f"Session {x['code']} ({x['year']})",
                            key="edit_session_select"
                        )
                        
                        if session_to_edit:
                            st.markdown(f"**Editing Session: {session_to_edit['code']}**")
                            
                            # Row 1: Group Selection (to allow moving sessions)
                            new_group_id = st.selectbox(
                                "Group",
                                options=[g['id'] for g in groups],
                                index=[g['id'] for g in groups].index(selected_group),
                                format_func=lambda x: f"{x} - {next(g['full_name'] for g in groups if g['id'] == x)}",
                                key="edit_group_select"
                            )
                            
                            # Row 2: Session Details
                            edit_col1, edit_col2, edit_col3 = st.columns(3)
                            with edit_col1:
                                new_code = st.text_input("Session Code", value=session_to_edit['code'], key="edit_code")
                            with edit_col2:
                                new_year = st.number_input("Year", min_value=1950, max_value=2100, value=session_to_edit['year'], key="edit_year")
                            with edit_col3:
                                new_dates = st.text_input("Dates", value=session_to_edit['dates'] if session_to_edit['dates'] else "", key="edit_dates")
                                
                            if st.button("💾 Save Changes", type="primary"):
                                try:
                                    SupabaseClient.update_session(
                                        session_id=session_to_edit['id'],
                                        group_id=new_group_id,
                                        code=new_code,
                                        year=new_year,
                                        dates=new_dates if new_dates else None
                                    )
                                    st.success(f"✅ Updated session {new_code}")
                                    if new_group_id != selected_group:
                                        st.info(f"🔄 Moved session to group {new_group_id}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating session: {e}")
                    else:
                        st.info("No sessions available to edit.")
    
    except Exception as e:
        st.error(f"Error: {e}")
