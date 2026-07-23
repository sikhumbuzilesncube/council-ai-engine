# app.py
# Professional Architect Dashboard for Bulawayo City Council
# With Side Navigation, Council Selection, and Profile Page

import streamlit as st
import json
import time
from datetime import datetime
import pandas as pd

# --- Supabase Imports ---
from supabase import create_client, Client

# --- AI Engine Imports ---
from engine import check_plan

# --- Page Configuration ---
st.set_page_config(
    page_title="Bulawayo City Council - Architect Portal",
    page_icon="🏗️",
    layout="wide"
)

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_ANON_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

# --- Helper Functions ---
def get_current_user():
    """Get the current logged-in user from session state."""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    return None

def login_user(email, password):
    """Login user with email and password."""
    if not supabase:
        return None, "Supabase not connected"
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            profile_response = supabase.table("profiles").select("*").eq("id", response.user.id).execute()
            profile = profile_response.data[0] if profile_response.data else {}
            st.session_state.user = {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": profile.get("full_name", ""),
                "architect_registration": profile.get("architect_registration", ""),
                "role": profile.get("role", "architect")
            }
            return st.session_state.user, None
        return None, "Login failed"
    except Exception as e:
        return None, str(e)

def register_user(email, password, full_name, architect_reg):
    """Register a new user."""
    if not supabase:
        return None, "Supabase not connected"
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            profile_data = {
                "id": response.user.id,
                "email": email,
                "full_name": full_name,
                "architect_registration": architect_reg,
                "role": "architect"
            }
            supabase.table("profiles").insert(profile_data).execute()
            st.session_state.user = {
                "id": response.user.id,
                "email": email,
                "full_name": full_name,
                "architect_registration": architect_reg,
                "role": "architect"
            }
            return st.session_state.user, None
        return None, "Registration failed"
    except Exception as e:
        return None, str(e)

def logout_user():
    """Logout the current user."""
    if supabase:
        supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

def save_plan_to_db(plan_data, result):
    """Save a plan submission to Supabase."""
    if not supabase or not get_current_user():
        return None, "Not logged in"
    try:
        user = get_current_user()
        submission = {
            "user_id": user["id"],
            "architect_name": user.get("full_name", ""),
            "architect_registration": user.get("architect_registration", ""),
            "council": plan_data.get("council"),
            "project_name": f"Plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "plot_area": plan_data.get("plot_area"),
            "building_footprint": plan_data.get("building_footprint"),
            "front_setback": plan_data.get("front_setback"),
            "side_setback": plan_data.get("side_setback"),
            "rear_setback": plan_data.get("rear_setback"),
            "total_height": plan_data.get("total_height"),
            "storey_height": plan_data.get("storey_height"),
            "num_storeys": plan_data.get("num_storeys"),
            "foundation_depth": plan_data.get("foundation_depth"),
            "foundation_width": plan_data.get("foundation_width"),
            "external_wall_thickness": plan_data.get("external_wall_thickness"),
            "internal_wall_thickness": plan_data.get("internal_wall_thickness"),
            "has_kitchen": plan_data.get("has_kitchen", False),
            "kitchen_window_area": plan_data.get("kitchen_window_area"),
            "other_window_area": plan_data.get("other_window_area"),
            "ventilation_area": plan_data.get("ventilation_area"),
            "ai_result": result,
            "status": "submitted"
        }
        response = supabase.table("plans").insert(submission).execute()
        return response.data, None
    except Exception as e:
        return None, str(e)

def get_user_plans():
    """Get all plans submitted by the current user."""
    if not supabase or not get_current_user():
        return []
    try:
        user = get_current_user()
        response = supabase.table("plans").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        return response.data
    except Exception:
        return []

# --- Authentication UI ---
def show_login_page():
    """Display the login/registration page."""
    st.markdown("""
        <style>
            .login-title { text-align: center; font-size: 2.5rem; font-weight: bold; color: #1a3a5c; }
            .login-subtitle { text-align: center; font-size: 1.1rem; color: #555; margin-bottom: 2rem; }
            .login-box { max-width: 450px; margin: 0 auto; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="login-title">🏗️ Bulawayo City Council</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Digital Plan Submission Portal</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            email = st.text_input("Email Address", placeholder="your@email.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            if st.button("Login", type="primary", use_container_width=True):
                if email and password:
                    user, error = login_user(email, password)
                    if user:
                        st.success("✅ Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Login failed: {error}")
                else:
                    st.warning("Please enter email and password")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            reg_email = st.text_input("Email Address", placeholder="your@email.com", key="reg_email")
            reg_password = st.text_input("Password", type="password", placeholder="Choose a strong password", key="reg_password")
            reg_full_name = st.text_input("Full Name", placeholder="e.g., John Smith", key="reg_name")
            reg_arch_reg = st.text_input("Architect Registration Number", placeholder="e.g., ARCH-1234", key="reg_arch")
            if st.button("Create Account", type="primary", use_container_width=True):
                if reg_email and reg_password and reg_full_name and reg_arch_reg:
                    user, error = register_user(reg_email, reg_password, reg_full_name, reg_arch_reg)
                    if user:
                        st.success("✅ Account created successfully! Please check your email to confirm.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ Registration failed: {error}")
                else:
                    st.warning("Please fill in all fields")
            st.markdown('</div>', unsafe_allow_html=True)

# --- Main Dashboard ---
def show_main_app():
    """Show the main application for logged-in users."""
    user = get_current_user()
    
    # --- Sidebar Navigation (THIS IS THE MISSING PART) ---
    with st.sidebar:
        st.markdown("### 🏗️ BCC Portal")
        st.markdown("---")
        
        if user:
            st.markdown(f"**👤 {user.get('full_name', 'Architect')}**")
            st.caption(f"📋 {user.get('architect_registration', 'N/A')}")
            st.caption(f"📧 {user.get('email', '')}")
        
        st.markdown("---")
        
        # Navigation Menu
        page = st.radio(
            "Menu",
            ["🏠 Dashboard", "📐 New Submission", "📂 My Submissions", "⚙️ Profile"],
            index=0
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
    
    # --- Page Content ---
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📐 New Submission":
        show_submission_form()
    elif page == "📂 My Submissions":
        show_submissions()
    else:
        show_profile()

# --- Dashboard Page ---
def show_dashboard():
    """Display the professional dashboard with stats and recent submissions."""
    user = get_current_user()
    plans = get_user_plans()
    
    # Welcome Banner
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a3a5c 0%, #2a5a8c 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; color: white;">
            <h1 style="margin: 0; font-size: 1.8rem;">👋 Welcome, {user.get('full_name', 'Architect')}!</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">You are logged into the Bulawayo City Council Digital Plan Submission Portal.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick Stats
    if plans:
        total = len(plans)
        pending = len([p for p in plans if p.get("status") in ["submitted", "under_review"]])
        approved = len([p for p in plans if p.get("status") == "approved"])
        rejected = len([p for p in plans if p.get("status") == "rejected"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Submissions", total)
        with col2:
            st.metric("⏳ Pending", pending)
        with col3:
            st.metric("✅ Approved", approved)
        with col4:
            st.metric("❌ Rejected", rejected)
    else:
        st.info("📭 You have no submissions yet. Click 'New Submission' to get started.")
    
    st.markdown("---")
    
    # Quick Action Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📐 Submit New Plan", type="primary", use_container_width=True):
            st.session_state.page = "📐 New Submission"
            st.rerun()
    
    st.markdown("---")
    
    # Recent Submissions Table
    if plans:
        st.subheader("📋 Recent Submissions")
        display_plan_table(plans[:10])
    else:
        st.info("📭 No submissions yet. Start by submitting your first plan!")

# --- Plan Table Display ---
def display_plan_table(plans):
    """Display a clean table of plans."""
    data = []
    for plan in plans:
        status_display = {
            "submitted": "⏳ Submitted",
            "under_review": "🔄 Under Review",
            "approved": "✅ Approved",
            "rejected": "❌ Rejected",
            "needs_revision": "🔄 Needs Revision"
        }
        status = plan.get("status", "submitted")
        data.append({
            "ID": plan.get("id", ""),
            "Date": plan.get("created_at", "")[:10] if plan.get("created_at") else "",
            "Council": plan.get("council", "N/A"),
            "Project": plan.get("project_name", "Untitled")[:30],
            "Status": status_display.get(status, status),
            "Passed": plan.get("ai_result", {}).get("passed_count", 0),
            "Failed": plan.get("ai_result", {}).get("failed_count", 0)
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- Submission Form (with Council Selection) ---
def show_submission_form():
    """Display the plan submission form."""
    st.header("📐 Submit New Building Plan")
    st.caption("Fill in the details below to submit your plan for AI review.")
    
    with st.form("submission_form"):
        # --- COUNCIL SELECTION (THIS IS THE NEW PART) ---
        col0_1, col0_2 = st.columns([1, 2])
        with col0_1:
            st.markdown("#### 🏛️ Submitting To")
        with col0_2:
            council = st.selectbox(
                "Select Local Authority",
                options=[
                    "City of Bulawayo",
                    "City of Harare",
                    "Gweru",
                    "Mutare",
                    "Masvingo",
                    "Mguza RDC",
                    "Mzingwane RDC"
                ],
                index=0
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📍 Site Details")
            plot_area = st.number_input("Plot Area (m²)", min_value=50, max_value=10000, value=500)
            building_footprint = st.number_input("Building Footprint (m²)", min_value=20, max_value=5000, value=250)
            
            st.markdown("#### 📏 Setbacks")
            front_setback = st.number_input("Front Setback (m)", min_value=0.0, max_value=50.0, value=4.0)
            side_setback = st.number_input("Side Setback (m)", min_value=0.0, max_value=50.0, value=2.0)
            rear_setback = st.number_input("Rear Setback (m)", min_value=0.0, max_value=50.0, value=3.0)
            
            st.markdown("#### 🧱 Foundations")
            foundation_depth = st.number_input("Foundation Depth (mm)", min_value=200, max_value=2000, value=600)
            foundation_width = st.number_input("Foundation Width (mm)", min_value=200, max_value=800, value=350)
        
        with col2:
            st.markdown("#### 📐 Building Height")
            total_height = st.number_input("Total Height (m)", min_value=2.0, max_value=50.0, value=10.5)
            storey_height = st.number_input("Storey Height (m)", min_value=2.0, max_value=5.0, value=2.6)
            num_storeys = st.number_input("Number of Storeys", min_value=1, max_value=10, value=3)
            
            st.markdown("#### 🧱 Walls")
            external_wall_thickness = st.number_input("External Wall Thickness (mm)", min_value=100, max_value=400, value=215)
            internal_wall_thickness = st.number_input("Internal Wall Thickness (mm)", min_value=80, max_value=300, value=100)
            
            st.markdown("#### 💡 Lighting & Ventilation")
            has_kitchen = st.checkbox("Plan includes a kitchen", value=True)
            kitchen_window_area = 0.0
            if has_kitchen:
                kitchen_window_area = st.number_input("Kitchen Window Area (% of floor area)", min_value=0.0, max_value=30.0, value=12.5)
            other_window_area = st.number_input("Other Rooms Window Area (% of floor area)", min_value=0.0, max_value=30.0, value=11.0)
            ventilation_area = st.number_input("Ventilation Area (% of floor area)", min_value=0.0, max_value=20.0, value=6.0)
        
        st.markdown("---")
        
        st.subheader("📎 Upload Plan File")
        uploaded_file = st.file_uploader("Upload your plan (PDF, PNG, JPG, or CAD file)", 
                                         type=["pdf", "png", "jpg", "jpeg", "dwg", "dxf"])
        
        submitted = st.form_submit_button("🚀 Submit Plan for Review", type="primary", use_container_width=True)
        
        if submitted:
            plan_data = {
                "council": council,
                "building_type": "residential",
                "plot_area": plot_area,
                "building_footprint": building_footprint,
                "front_setback": front_setback,
                "side_setback": side_setback,
                "rear_setback": rear_setback,
                "total_height": total_height,
                "storey_height": storey_height,
                "num_storeys": num_storeys,
                "foundation_depth": foundation_depth,
                "foundation_width": foundation_width,
                "external_wall_thickness": external_wall_thickness,
                "internal_wall_thickness": internal_wall_thickness,
                "has_kitchen": has_kitchen,
                "kitchen_window_area": kitchen_window_area if has_kitchen else None,
                "other_window_area": other_window_area,
                "ventilation_area": ventilation_area
            }
            
            with st.spinner("🤖 AI is reviewing your plan..."):
                result = check_plan(plan_data)
            
            if supabase:
                saved, error = save_plan_to_db(plan_data, result)
                if saved:
                    st.success("✅ Plan submitted and saved to the system!")
                else:
                    st.warning(f"⚠️ Plan checked but could not be saved: {error}")
            
            st.markdown("---")
            display_ai_results(result)

# --- Display AI Results ---
def display_ai_results(result):
    """Display the AI inspection report."""
    st.subheader("📋 AI Inspection Report")
    
    if result["status"] == "PASSED":
        st.success("✅ **PLAN PASSED!** Your plan complies with all checked by-laws.")
    else:
        st.error("❌ **PLAN FAILED!** The following violations were found:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rules Checked", result["total_rules_checked"])
    with col2:
        st.metric("Passed", result["passed_count"])
    with col3:
        st.metric("Failed", result["failed_count"])
    
    if result["violations"]:
        st.subheader("🚫 Violations Found")
        for v in result["violations"]:
            with st.expander(f"❌ {v['rule_id']}: {v['rule_name']}"):
                st.write(f"**Message:** {v['message']}")
                st.write(f"**Your Value:** {v['value_provided']}")
                st.write(f"**Required:** {v['threshold']}")
    else:
        st.balloons()
        st.success("🎉 No violations found! Your plan is compliant.")

# --- Submission History ---
def show_submissions():
    """Display the user's submission history."""
    st.header("📂 My Submissions")
    
    plans = get_user_plans()
    if not plans:
        st.info("📭 You have no submissions yet. Click 'New Submission' to get started.")
        return
    
    display_plan_table(plans)
    
    st.markdown("---")
    st.caption("💡 Click on a row above to view full details (coming soon)")

# --- Profile Page ---
def show_profile():
    """Display the user's profile information."""
    user = get_current_user()
    
    st.header("⚙️ My Profile")
    
    if user:
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px;">
            <p><strong>👤 Full Name:</strong> {user.get('full_name', 'N/A')}</p>
            <p><strong>📧 Email:</strong> {user.get('email', 'N/A')}</p>
            <p><strong>📋 Architect Registration:</strong> {user.get('architect_registration', 'N/A')}</p>
            <p><strong>🔑 Role:</strong> {user.get('role', 'Architect').capitalize()}</p>
            <p><strong>🆔 User ID:</strong> {user.get('id', 'N/A')[:8]}...</p>
        </div>
        """, unsafe_allow_html=True)

# --- Main App Logic ---
def main():
    user = get_current_user()
    
    if user:
        show_main_app()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
