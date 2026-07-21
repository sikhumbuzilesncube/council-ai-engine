# app.py
# Web Portal for Architects - Plan Submission and AI Checking
# Deployed on Streamlit Cloud with Supabase Integration

import streamlit as st
import json
from supabase import create_client, Client
import os
from engine import check_plan

# --- Supabase Configuration ---
# You will add your Supabase URL and Anon Key later
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", "")

if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None

# --- Page Setup ---
st.set_page_config(page_title="City Council - Plan Submission", layout="wide")

st.title("🏗️ City Council Building Plan Submission Portal")
st.subheader("Submit your residential building plan for AI review")

# --- Sidebar: Instructions ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/city-hall.png", width=80)
    st.header("Instructions")
    st.markdown("""
    1. Fill in all measurements below.
    2. The AI will check your plan against the Model Building By-laws.
    3. You will receive a report with any violations.
    4. Fix the issues and resubmit for approval.
    """)
    st.markdown("---")
    st.caption("Powered by AI Rules Engine v1.0")

# --- Main Form ---
with st.form("plan_submission_form"):
    st.header("📐 Building Measurements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Site Details")
        plot_area = st.number_input("Plot Area (square meters)", min_value=100, max_value=10000, value=500)
        building_footprint = st.number_input("Building Footprint (square meters)", min_value=50, max_value=5000, value=250)
        
        st.subheader("Setbacks")
        front_setback = st.number_input("Front Setback (meters)", min_value=0.0, max_value=50.0, value=4.0)
        side_setback = st.number_input("Side Setback (meters)", min_value=0.0, max_value=50.0, value=2.0)
        rear_setback = st.number_input("Rear Setback (meters)", min_value=0.0, max_value=50.0, value=3.0)
    
    with col2:
        st.subheader("Building Height")
        total_height = st.number_input("Total Building Height (meters)", min_value=2.0, max_value=50.0, value=10.5)
        storey_height = st.number_input("Storey Height (meters)", min_value=2.0, max_value=5.0, value=2.6)
        num_storeys = st.number_input("Number of Storeys", min_value=1, max_value=10, value=3)
        
        st.subheader("Foundations")
        foundation_depth = st.number_input("Foundation Depth (mm)", min_value=200, max_value=2000, value=600)
        foundation_width = st.number_input("Foundation Width - Sleeper Walls (mm)", min_value=200, max_value=800, value=350)
        
        st.subheader("Walls")
        external_wall_thickness = st.number_input("External Wall Thickness (mm)", min_value=100, max_value=400, value=215)
        internal_wall_thickness = st.number_input("Internal Wall Thickness (mm)", min_value=80, max_value=300, value=100)
    
    st.subheader("💡 Lighting & Ventilation")
    col3, col4 = st.columns(2)
    
    with col3:
        has_kitchen = st.checkbox("Does the plan include a kitchen?", value=True)
        kitchen_window_area = 0.0
        if has_kitchen:
            kitchen_window_area = st.number_input("Kitchen Window Area (% of floor area)", min_value=0.0, max_value=30.0, value=12.5)
        other_window_area = st.number_input("Other Habitable Rooms - Window Area (% of floor area)", min_value=0.0, max_value=30.0, value=11.0)
    
    with col4:
        ventilation_area = st.number_input("Ventilation Area (% of floor area)", min_value=0.0, max_value=20.0, value=6.0)
    
    # --- Submit Button ---
    submitted = st.form_submit_button("🚀 Run AI Check", type="primary")
    
    if submitted:
        # Build the plan_data dictionary
        plan_data = {
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
        
        # Run the AI check
        with st.spinner("🤖 AI is checking your plan against the by-laws..."):
            result = check_plan(plan_data)
        
        # Save to Supabase if connected
        if supabase:
            try:
                submission_data = {
                    "plan_data": plan_data,
                    "result": result,
                    "user_id": "anonymous"  # Will be replaced with actual user ID later
                }
                supabase.table("plan_submissions").insert(submission_data).execute()
                st.success("📁 Plan saved to database!")
            except Exception as e:
                st.warning(f"⚠️ Could not save to database: {e}")
        
        # Display results
        st.markdown("---")
        st.header("📋 AI Inspection Report")
        
        # Status
        if result["status"] == "PASSED":
            st.success("✅ **PLAN PASSED!** Your plan complies with all checked by-laws.")
        else:
            st.error("❌ **PLAN FAILED!** The following violations were found:")
        
        # Summary stats
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric("Rules Checked", result["total_rules_checked"])
        with col6:
            st.metric("Passed", result["passed_count"])
        with col7:
            st.metric("Failed", result["failed_count"])
        
        # Show violations
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
