import streamlit as st
import pandas as pd
from auth_utils import require_auth, check_permission
from supabase_client import SupabaseClient
import time

# 1. Page Config
st.set_page_config(page_title="User Management", page_icon="👥", layout="wide")

# 2. Auth Check
require_auth()

# 3. Permission Check (Admin Only)
if not check_permission('admin'):
    st.error("⛔ Access Denied: You need Administrator privileges to view this page.")
    st.image("https://media.giphy.com/media/njYrp176NnVIn3rfkp/giphy.gif")
    st.stop()

st.title("👥 User Management")
st.markdown("Manage user roles and permissions.")

# 4. Fetch Users
with st.spinner("Loading users..."):
    try:
        profiles = SupabaseClient.get_all_profiles()
    except Exception as e:
        st.error(f"❌ Error fetching users: {e}")
        profiles = []

if not profiles:
    if "profiles" not in locals(): # handle case where profiles wasn't assigned due to crash
        pass
    else:
        st.info("No users found yet.")
else:
    # Convert to DataFrame for display
    df = pd.DataFrame(profiles)
    
    # Reorder columns for better view
    cols = ['email', 'role', 'full_name', 'created_at', 'id']
    # Filter only columns that exist
    cols = [c for c in cols if c in df.columns]
    df = df[cols]

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", len(profiles))
    col2.metric("Admins", len(df[df['role'] == 'admin']))
    col3.metric("New (Last 7 Days)", len(df)) # Placeholder logic

# 5. User Creation (Top Section)
with st.expander("➕ Create New User", expanded=False):
    c1, c2, c3 = st.columns(3)
    new_email = c1.text_input("New User Email")
    new_pass = c2.text_input("Password", type="password")
    new_name = c3.text_input("Full Name")
    
    if st.button("Create User"):
        if not new_email or not new_pass:
            st.error("Email and Password are required.")
        else:
            with st.spinner("Creating user..."):
                try:
                    success = SupabaseClient.create_user(new_email, new_pass, new_name)
                    if success:
                        st.success(f"User {new_email} created successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to create user (Unknown reason).")
                except Exception as e:
                     st.error(f"❌ Creation Failed: {str(e)}")

st.markdown("---")

# 6. User Table & Management
st.subheader("User List")

# Use columns to create a layout: Table on Left, Edit Form on Right
left_col, right_col = st.columns([2, 1])

with left_col:
    st.dataframe(
        df, 
        use_container_width=True,
        column_config={
            "created_at": st.column_config.DatetimeColumn("Joined At", format="D MMM YYYY"),
            "email": "Email Address",
            "role": st.column_config.TextColumn(
                "Role", 
                help="User permission level",
                width="small"
            ),
        },
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun" # Useful for future interactivity
    )

with right_col:
    st.markdown("### ✏️ Manage User")
    
    # Select User
    # Create a list of "Email (Role)" for the dropdown
    user_options = {f"{p.get('email', 'No Email')} ({p.get('role')})": p for p in profiles}
    
    selected_label = st.selectbox(
        "Select User to Action", 
        options=list(user_options.keys()),
        index=None,
        placeholder="Choose a user..."
    )

    if selected_label:
        selected_user = user_options[selected_label]
        current_role = selected_user.get('role')
        user_id = selected_user.get('id')
        user_email = selected_user.get('email')

        st.info(f"Selected: **{user_email}**")
        
        # --- EDIT ROLE ---
        st.markdown("#### Change Role")
        new_role = st.selectbox(
            "New Role",
            ["basic", "advanced", "collaborator", "admin"],
            index=["basic", "advanced", "collaborator", "admin"].index(current_role) if current_role in ["basic", "advanced", "collaborator", "admin"] else 0
        )

        if new_role != current_role:
            if st.button(f"Update to {new_role.upper()}", type="primary", use_container_width=True):
                with st.spinner("Updating..."):
                    success = SupabaseClient.update_user_role(user_id, new_role)
                    if success:
                        st.success(f"Updated {user_email} to {new_role}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Update failed. Check DB permissions.")
        
        st.markdown("---")
        
        # --- DELETE USER ---
        st.markdown("#### Danger Zone")
        if st.button(f"🗑️ Delete {user_email}", type="secondary", use_container_width=True):
             # Double confirm using a hack or just strict warning? Streamlit doesn't have modal dialogs easily.
             # We will rely on the user being Admin.
             with st.spinner("Deleting..."):
                try:
                    success = SupabaseClient.delete_user(user_id)
                    if success:
                        st.success(f"User {user_email} deleted!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                     st.error(f"❌ Deletion Failed: {str(e)}")

