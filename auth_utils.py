"""
Authentication Utilities for WP29 Archive
Handles login, logout, and session state management
"""
import streamlit as st
import time
import datetime
from supabase_client import SupabaseClient
from config import Config

import extra_streamlit_components as stx

# Initialize Cookie Manager (Cached to avoid reloading)
@st.cache_resource
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

def init_auth():
    """Initialize session state for auth and check persistence"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'role' not in st.session_state:
        st.session_state['role'] = None
        
    # Check for persistence cookie if not already authenticated
    if not st.session_state['authenticated']:
        try:
            # We store the user ID in the cookie. 
            # SECURITY NOTE: In a real prod app, use a secure session token, not just ID.
            # For this internal tool, we'll accept the risk for convenience as requested.
            user_id = cookie_manager.get('wp29_auth_user')
            
            if user_id:
                # Valid cookie found, attempt auto-login logic
                # We need to fetch the user profile to confirm validity
                # (Note: Supabase client normally needs a full session, 
                # but we'll re-use the service role or anon key to just get the profile/role)
                
                # Verify user exists and get role
                role = SupabaseClient.get_user_role(user_id)
                
                if role: # If we successfully got a role, the user ID is valid
                    # Mock a user object since we don't have the full supabase session object from just an ID
                    # Ideally we would use a Refresh Token, but Streamlit cookies are simpler this way for now.
                    
                    # Fetch email for display
                    client = SupabaseClient.get_client()
                    # We can't easily get the email from just ID without admin rights in some setups,
                    # but let's try reading our 'profiles' table which we control.
                    profile = client.table('profiles').select('email').eq('id', user_id).execute()
                    
                    email = "Persistent User"
                    if profile.data:
                        email = profile.data[0].get('email', email)
                        
                    class MockUser:
                        def __init__(self, id, email):
                            self.id = id
                            self.email = email
                    
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = MockUser(user_id, email)
                    st.session_state['role'] = role
                    # st.toast(f"Restored session for {email}")
        except Exception as e:
            # Cookie invalid or other error
            print(f"Auth persistence error: {e}")

def login_form():
    """Display the login form"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.title("🔐 Login")
        st.markdown("Please sign in to access the UNECE Archive.")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign In", use_container_width=True):
            if not email or not password:
                st.error("Please enter email and password")
                return
            
            with st.spinner("Authenticating..."):
                try:
                    client = SupabaseClient.get_client()
                    auth_response = client.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    if auth_response.user:
                        st.session_state['authenticated'] = True
                        st.session_state['user'] = auth_response.user
                        
                        # Fetch Role
                        user_id = auth_response.user.id
                        role = SupabaseClient.get_user_role(user_id)
                        st.session_state['role'] = role
                        
                        st.success(f"Welcome back! ({role})")
                        time.sleep(1)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")

def render_sidebar():
    """Render custom sidebar with navigation and user status"""
    
    # 1. Hide Default Streamlit Navigation
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.title("UNECE Archive")
        
        # 1. User Status (Moved to top)
        if st.session_state.get('user'):
            email = st.session_state['user'].email
            role = st.session_state.get('role', 'basic')
            
            st.markdown(f"**User**: `{email}`")
            st.markdown(f"**Role**: `{role.upper()}`")
            
            if st.button("Log Out", use_container_width=True):
                client = SupabaseClient.get_client()
                client.auth.sign_out()
                
                # Clear persistence cookie
                cookie_manager.delete('wp29_auth_user')
                
                st.session_state['authenticated'] = False
                st.session_state['user'] = None
                st.session_state['role'] = None
                st.rerun()
            st.markdown("---")
        
        # 2. Navigation
        st.subheader("Navigation")
        
        # Public / All Users
        st.page_link("Home.py", label="Home", icon="🏠")
        
        # Authenticated Users Only
        if st.session_state.get('authenticated'):
            st.page_link("pages/4_Search_Session.py", label="Search Documents", icon="🔍")
            st.page_link("pages/5_Adopted_Proposals.py", label="Adopted Proposals", icon="📜")
            st.page_link("pages/3_Regulation_Library.py", label="Regulations", icon="📚")
            st.page_link("pages/3_Interpretation_Library.py", label="Interpretations", icon="💡")
            st.page_link("pages/5_AI_Assistant.py", label="AI Assistant", icon="🤖")
            st.page_link("pages/Mobile_Chat.py", label="AI Assistant Light ⚡", icon="⚡")
            st.page_link("pages/7_Organization_Chart.py", label="Org Chart", icon="📊")
            st.page_link("pages/6_Report_Generator.py", label="Report Generator", icon="📝")
            st.page_link("pages/My_Meetings.py", label="My Meetings", icon="📅")
            
            # Collaborator Only
            if check_permission('collaborator'):
                st.markdown("---")
                st.markdown("### 🛠️ Admin Area")
                st.page_link("pages/1_Admin_Structure.py", label="Admin Structure", icon="🏛️")
                st.page_link("pages/2_Smart_Ingestion.py", label="Smart Ingestion", icon="📤")
                
            # Admin Only
            if check_permission('admin'):
                st.page_link("pages/8_User_Management.py", label="User Management", icon="👥")
            st.page_link("pages/99_Debug_Keys.py", label="Debug Keys 🐞", icon="🐞")

            # End of Sidebar
            # End of Sidebar
            st.markdown("---")
            st.markdown(f"**App Version:** `{Config.APP_VERSION}`")
            st.caption(f"Date: {Config.APP_DATE}")

# Update Login Logic to set cookie
def login_form():
    """Display the login form"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.title("🔐 Login")
        st.markdown("Please sign in to access the UNECE Archive.")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign In", use_container_width=True):
            if not email or not password:
                st.error("Please enter email and password")
                return
            
            with st.spinner("Authenticating..."):
                try:
                    client = SupabaseClient.get_client()
                    auth_response = client.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    if auth_response.user:
                        st.session_state['authenticated'] = True
                        st.session_state['user'] = auth_response.user
                        
                        # Fetch Role
                        user_id = auth_response.user.id
                        role = SupabaseClient.get_user_role(user_id)
                        st.session_state['role'] = role
                        
                        # SET PERSISTENCE COOKIE (Expires in 30 days)
                        cookie_manager.set('wp29_auth_user', user_id, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        
                        st.success(f"Welcome back! ({role})")
                        time.sleep(1)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")

def require_auth():
    """Guard clause to protect pages"""
    init_auth()
    
    # Always render sidebar (it handles hiding/showing links internally)
    render_sidebar()
    
    if not st.session_state['authenticated']:
        st.warning("Please log in to access this page")
        st.page_link("Home.py", label="Go to Login Page 🔐", icon="🔐")
        st.stop()

def check_permission(required_role: str) -> bool:
    """
    Check if current user has permission.
    Hierarchy: admin > collaborator > advanced > basic
    """
    if not st.session_state.get('role'):
        return False
        
    role = st.session_state['role']
    
    levels = {
        'basic': 1,
        'advanced': 2,
        'collaborator': 3,
        'admin': 4
    }
    
    user_level = levels.get(role, 0)
    req_level = levels.get(required_role, 100)
    
    return user_level >= req_level
