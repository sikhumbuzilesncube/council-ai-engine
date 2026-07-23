# app.py
# Bulawayo City Council - Architect Portal (New Layout)

import streamlit as st
import time
from datetime import datetime
import pandas as pd
from supabase import create_client

# --- AI Engine ---
from engine import check_plan

# --- Page Config ---
st.set_page_config(
    page_title="BCC Architect Portal",
    page_icon="🏗️",
    layout="wide"
)

# --- Supabase ---
@st.cache_resource
def get_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_ANON_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase = get_supabase()

# --- Session State ---
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# --- Auth Functions ---
def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            profile = supabase.table("profiles").select("*").eq("id", res.user.id).execute()
            p = profile.data[0] if profile.data else {}
            st.session_state.user = {
                "id": res.user.id,
                "email": res.user.email,
                "full_name": p.get("full_name", ""),
                "architect_registration": p.get("architect_registration", ""),
                "role": p.get("role", "architect")
            }
            return True, None
        return False, "Login failed"
    except Exception as e:
        return False, str(e)

def register_user(email, password, full_name, arch_reg):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({
                "id": res.user.id,
                "email": email,
                "full_name": full_name,
                "architect_registration": arch_reg,
                "role": "architect"
            }).execute()
            st.session_state.user = {
                "id": res.user.id,
                "email": email,
                "full_name": full_name,
                "architect_registration": arch_reg,
                "role": "architect"
            }
            return True, None
        return False, "Registration failed"
    except Exception as e:
        return False, str(e)

def logout():
    if supabase:
        supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.page = "dashboard"
    st.rerun()

def get_plans():
    if not supabase or not st.session_state.user:
        return []
    try:
        res = supabase.table("plans").select("*").eq("user_id", st.session_state.user["id"]).order("created_at", desc=True).execute()
        return res.data
    except:
        return []

def save_plan(data, result):
    if not supabase or not st.session_state.user:
        return None, "Not logged in"
    try:
        submission = {
            "user_id": st.session_state.user["id"],
            "architect_name": st.session_state.user.get("full_name", ""),
            "architect_registration": st.session_state.user.get("architect_registration", ""),
            "council": data.get("council"),
            "project_name": f"Plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "plot_area": data.get("plot_area"),
            "building_footprint": data.get("building_footprint"),
            "front_setback": data.get("front_setback"),
            "side_setback": data.get("side_setback"),
            "rear_setback": data.get("rear_setback"),
            "total_height": data.get("total_height"),
            "storey_height": data.get("storey_height"),
            "num_storeys": data.get("num_storeys"),
            "foundation_depth": data.get("foundation_depth"),
            "foundation_width": data.get("foundation_width"),
            "external_wall_thickness": data.get("external_wall_thickness"),
            "internal_wall_thickness": data.get("internal_wall_thickness"),
            "has_kitchen": data.get("has_kitchen", False),
            "kitchen_window_area": data.get("kitchen_window_area"),
            "other_window_area": data.get("other_window_area"),
            "ventilation_area": data.get("ventilation_area"),
            "ai_result": result,
            "status": "submitted"
        }
        res = supabase.table("plans").insert(submission).execute()
        return res.data, None
    except Exception as e:
        return None, str(e)

# --- Login Page ---
def show_login():
    st.markdown("""
        <style>
            .main-title { text-align: center; font-size: 2.8rem; font-weight: bold; color: #1a3a5c; margin-top: 2rem; }
            .sub-title { text-align: center; font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
            .auth-box { max-width: 420px; margin: 0 auto; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-title">🏗️ Bulawayo City Council</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Digital Plan Submission Portal</p>', unsafe_allow_html=True)
    
    if not supabase:
        st.error("⚠️ Supabase not connected. Please check your secrets.")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        with st.container():
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="your@email.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
            if st.button("Login", type="primary", use_container_width=True):
                if email and password:
                    ok, err = login_user(email, password)
                    if ok:
                        st.success("✅ Logged in!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {err}")
                else:
                    st.warning("Please fill in all fields")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        with st.container():
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            reg_email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
            reg_pass = st.text_input("Password", type="password", placeholder="Choose a strong password", key="reg_pass")
            reg_name = st.text_input("Full Name", placeholder="e.g., John Smith", key="reg_name")
            reg_arch = st.text_input("Architect Registration", placeholder="e.g., ARCH-1234", key="reg_arch")
            if st.button("Create Account", type="primary", use_container_width=True):
                if reg_email and reg_pass and reg_name and reg_arch:
                    ok, err = register_user(reg_email, reg_pass, reg_name, reg_arch)
                    if ok:
                        st.success("✅ Account created! Please check your email to confirm.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {err}")
                else:
                    st.warning("Please fill in all fields")
            st.markdown('</div>', unsafe_allow_html=True)

# --- Dashboard ---
def show_dashboard():
    user = st.session_state.user
    plans = get_plans()
    
    # Welcome Banner
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a3a5c 0%, #2a5a8c 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; color: white;">
            <h1 style="margin: 0; font-size: 1.8rem;">👋 Welcome, {user.get('full_name', 'Architect')}!</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">Bulawayo City Council Digital Plan Submission Portal</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Stats
    if plans:
        total = len(plans)
        pending = len([p for p in plans if p.get("status") in ["submitted", "under_review"]])
        approved = len([p for p in plans if p.get("status") == "approved"])
        rejected = len([p for p in plans if p.get("status") == "rejected"])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📊 Total", total)
        c2.metric("⏳ Pending", pending)
        c3.metric("✅ Approved", approved)
        c4.metric("❌ Rejected", rejected)
    else:
        st.info("📭 You have no submissions yet.")
    
    st.markdown("---")
    
    # Quick Actions
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("📐 New Submission", type="primary", use_container_width=True):
            st.session_state.page = "new"
            st.rerun()
    with c2:
        if st.button("📂 My Submissions", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
    with c3:
        if st.button("⚙️ Profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
    
    # Recent Submissions
    if plans:
        st.markdown("---")
        st.subheader("📋 Recent Submissions")
        data = []
        for p in plans[:5]:
            data.append({
                "ID": p.get("id", ""),
                "Date": p.get("created_at", "")[:10],
                "Council": p.get("council", "N/A"),
                "Status": p.get("status", "submitted").title(),
                "Passed": p.get("ai_result", {}).get("passed_count", 0),
                "Failed": p.get("ai_result", {}).get("failed_count", 0)
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- New Submission ---
def show_submission():
    st.header("📐 Submit New Building Plan")
    
    with st.form("plan_form"):
        # Council Selection
        council = st.selectbox(
            "🏛️ Select Local Authority",
            ["City of Bulawayo", "City of Harare", "Gweru", "Mutare", "Masvingo", "Mguza RDC", "Mzingwane RDC"]
        )
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Site & Setbacks")
            plot_area = st.number_input("Plot Area (m²)", min_value=50, max_value=10000, value=500)
            building_footprint = st.number_input("Building Footprint (m²)", min_value=20, max_value=5000, value=250)
            front_setback = st.number_input("Front Setback (m)", min_value=0.0, max_value=50.0, value=4.0)
            side_setback = st.number_input("Side Setback (m)", min_value=0.0, max_value=50.0, value=2.0)
            rear_setback = st.number_input("Rear Setback (m)", min_value=0.0, max_value=50.0, value=3.0)
        
        with c2:
            st.subheader("Height, Walls & Foundations")
            total_height = st.number_input("Total Height (m)", min_value=2.0, max_value=50.0, value=10.5)
            storey_height = st.number_input("Storey Height (m)", min_value=2.0, max_value=5.0, value=2.6)
            num_storeys = st.number_input("Number of Storeys", min_value=1, max_value=10, value=3)
            foundation_depth = st.number_input("Foundation Depth (mm)", min_value=200, max_value=2000, value=600)
            foundation_width = st.number_input("Foundation Width (mm)", min_value=200, max_value=800, value=350)
            external_wall_thickness = st.number_input("External Wall (mm)", min_value=100, max_value=400, value=215)
            internal_wall_thickness = st.number_input("Internal Wall (mm)", min_value=80, max_value=300, value=100)
        
        st.subheader("💡 Lighting & Ventilation")
        c3, c4 = st.columns(2)
        with c3:
            has_kitchen = st.checkbox("Includes a kitchen", value=True)
            kitchen_window = 0.0
            if has_kitchen:
                kitchen_window = st.number_input("Kitchen Window Area (% of floor)", min_value=0.0, max_value=30.0, value=12.5)
        with c4:
            other_window = st.number_input("Other Rooms Window Area (% of floor)", min_value=0.0, max_value=30.0, value=11.0)
            ventilation = st.number_input("Ventilation Area (% of floor)", min_value=0.0, max_value=20.0, value=6.0)
        
        uploaded = st.file_uploader("📎 Upload Plan File", type=["pdf", "png", "jpg", "jpeg", "dwg", "dxf"])
        
        submitted = st.form_submit_button("🚀 Submit Plan", type="primary", use_container_width=True)
        
        if submitted:
            data = {
                "council": council,
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
                "kitchen_window_area": kitchen_window if has_kitchen else None,
                "other_window_area": other_window,
                "ventilation_area": ventilation
            }
            
            with st.spinner("🤖 AI is reviewing..."):
                result = check_plan(data)
            
            if supabase:
                saved, err = save_plan(data, result)
                if saved:
                    st.success("✅ Plan submitted and saved!")
                else:
                    st.warning(f"⚠️ Could not save: {err}")
            
            st.markdown("---")
            
            # Results
            if result["status"] == "PASSED":
                st.success("✅ **PLAN PASSED!**")
            else:
                st.error("❌ **PLAN FAILED!**")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Rules Checked", result["total_rules_checked"])
            col2.metric("Passed", result["passed_count"])
            col3.metric("Failed", result["failed_count"])
            
            for v in result["violations"]:
                with st.expander(f"❌ {v['rule_id']}: {v['rule_name']}"):
                    st.write(f"**Message:** {v['message']}")
                    st.write(f"**Your Value:** {v['value_provided']}")
                    st.write(f"**Required:** {v['threshold']}")
            
            if not result["violations"]:
                st.balloons()
                st.success("🎉 No violations found!")

# --- History ---
def show_history():
    st.header("📂 My Submissions")
    plans = get_plans()
    if not plans:
        st.info("📭 No submissions yet.")
        return
    data = []
    for p in plans:
        data.append({
            "ID": p.get("id"),
            "Date": p.get("created_at", "")[:10],
            "Council": p.get("council", "N/A"),
            "Status": p.get("status", "submitted").title(),
            "Passed": p.get("ai_result", {}).get("passed_count", 0),
            "Failed": p.get("ai_result", {}).get("failed_count", 0)
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- Profile ---
def show_profile():
    user = st.session_state.user
    st.header("⚙️ My Profile")
    st.markdown(f"""
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px;">
            <p><strong>👤 Full Name:</strong> {user.get('full_name', 'N/A')}</p>
            <p><strong>📧 Email:</strong> {user.get('email', 'N/A')}</p>
            <p><strong>📋 Architect Registration:</strong> {user.get('architect_registration', 'N/A')}</p>
            <p><strong>🔑 Role:</strong> {user.get('role', 'Architect').capitalize()}</p>
        </div>
    """, unsafe_allow_html=True)

# --- Main Navigation ---
def main():
    if not st.session_state.user:
        show_login()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 2.5rem;">🏗️</div>
                <div style="font-weight: bold; font-size: 1.1rem; margin-top: 0.5rem;">BCC Portal</div>
                <div style="font-size: 0.8rem; color: #888;">{st.session_state.user.get('full_name', 'Architect')}</div>
                <div style="font-size: 0.7rem; color: #aaa;">{st.session_state.user.get('architect_registration', '')}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("📐 New Submission", use_container_width=True):
            st.session_state.page = "new"
            st.rerun()
        
        if st.button("📂 My Submissions", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
        
        if st.button("⚙️ Profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Page Content
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "new":
        show_submission()
    elif st.session_state.page == "history":
        show_history()
    elif st.session_state.page == "profile":
        show_profile()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
