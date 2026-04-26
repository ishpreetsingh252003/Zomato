import streamlit as st
import sys
import pandas as pd
from pathlib import Path
import time
import os

# --- PATH CONFIGURATION ---
_ARCH_DIR = Path(__file__).resolve().parent.parent
p6_backend_dir = str(_ARCH_DIR / "phase_6_monitoring" / "backend")
if p6_backend_dir not in sys.path:
    sys.path.insert(0, p6_backend_dir)
p6_dir = str(_ARCH_DIR / "phase_6_monitoring")
if p6_dir not in sys.path:
    sys.path.insert(0, p6_dir)

import orchestrator
import analytics_logger

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="Zomato AI Recommendations", layout="wide", page_icon="🍽️")

# --- CUSTOM CSS ---
st.markdown("""
<style>
div.stButton > button {
    border-radius: 20px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Zomato AI")
st.sidebar.markdown("Phase 7 Deployment")
page = st.sidebar.radio("Navigation", ["🔍 Find Restaurants", "📊 Analytics Dashboard"])

# --- CACHED METADATA ---
@st.cache_data(ttl=3600)
def load_metadata():
    try:
        return orchestrator.get_metadata()
    except Exception as e:
        return {"locations": ["Bangalore", "Indiranagar", "Koramangala"], "cuisines": ["Italian", "Chinese", "Cafe", "North Indian"]}

metadata = load_metadata()

# =========================================================================
# PAGE 1: USER UI
# =========================================================================
if page == "🔍 Find Restaurants":
    st.title("Find your perfect restaurant")
    st.markdown("Describe your preferences and our AI ranks the best options with clear, personalised explanations.")
    
    with st.form("preference_form"):
        col1, col2 = st.columns(2)
        with col1:
            location = st.selectbox("📍 Location", metadata.get("locations", ["Bangalore"]))
            budget_raw = st.slider("💰 Budget (₹)", min_value=200, max_value=4000, value=1000, step=100)
        with col2:
            cuisines = st.selectbox("🍜 Cuisine", ["Any"] + metadata.get("cuisines", []))
            min_rating = st.slider("⭐ Minimum Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
        
        optional_prefs = st.text_input("✨ Optional Preferences (comma-separated)", "quick-service")
        top_n = st.selectbox("🏆 Number of Results", [1, 3, 5, 10], index=2)
        
        submitted = st.form_submit_button("Get Recommendations ➔")
    
    if submitted:
        # Convert budget to categories expected by engine
        budget_str = "low" if budget_raw <= 600 else ("medium" if budget_raw <= 1500 else "high")
        cuisine_list = [] if cuisines == "Any" else [cuisines]
        opt_prefs_list = [p.strip() for p in optional_prefs.split(",") if p.strip()]
        
        preferences = {
            "location": location,
            "budget": budget_str,
            "cuisines": cuisine_list,
            "min_rating": min_rating,
            "optional_preferences": opt_prefs_list
        }
        
        with st.spinner("Finding the best restaurants using AI..."):
            start_time = time.time()
            try:
                result = orchestrator.run_pipeline(preferences, top_n=top_n)
                latency_ms = (time.time() - start_time) * 1000.0
                
                recs = result.get("recommendations", [])
                query_id = analytics_logger.log_query(preferences, len(recs), latency_ms)
                
                st.subheader(f"Top {len(recs)} Recommendations")
                st.caption(f"Source: {result.get('source', 'unknown').upper()}")
                
                for rec in recs:
                    with st.container():
                        st.markdown(f"### #{rec['rank']} {rec['restaurant_name']}")
                        st.markdown(f"**{rec.get('cuisine', '')}** | ⭐ {rec.get('rating', 'N/A')} | 💸 ₹{rec.get('cost_for_two', 'N/A')} for 2")
                        st.info(f"**Why recommended:** {rec.get('explanation', '')}")
                        
                        # Interactive Feedback Buttons
                        col_like, col_dislike, _ = st.columns([1, 1, 8])
                        with col_like:
                            if st.button("👍", key=f"like_{query_id}_{rec['rank']}"):
                                analytics_logger.log_feedback(query_id, rec['restaurant_name'], "like")
                                st.toast("Feedback submitted! Thanks.")
                        with col_dislike:
                            if st.button("👎", key=f"dislike_{query_id}_{rec['rank']}"):
                                analytics_logger.log_feedback(query_id, rec['restaurant_name'], "dislike")
                                st.toast("Feedback submitted! Thanks.")
                        st.divider()
                        
            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# =========================================================================
# PAGE 2: ANALYTICS DASHBOARD
# =========================================================================
elif page == "📊 Analytics Dashboard":
    st.title("📊 Zomato AI Analytics")
    st.markdown("Monitor queries, latency, and user feedback to tune AI performance.")
    
    try:
        conn = analytics_logger._get_connection()
        queries_df = pd.read_sql("SELECT * FROM queries", conn)
        feedback_df = pd.read_sql("SELECT * FROM feedback", conn)
        conn.close()
    except Exception as e:
        st.error(f"Failed to load analytics DB: {e}")
        st.stop()
        
    if queries_df.empty:
        st.info("No data available yet.")
        st.stop()
        
    total_queries = len(queries_df)
    avg_latency = queries_df['latency_ms'].mean() / 1000.0
    total_feedback = len(feedback_df)
    likes = len(feedback_df[feedback_df['feedback_type'] == 'like'])
    like_ratio = (likes / total_feedback * 100) if total_feedback > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Queries", total_queries)
    col2.metric("Avg Latency", f"{avg_latency:.2f}s")
    col3.metric("Total Feedback", total_feedback)
    col4.metric("Like Ratio", f"{like_ratio:.1f}%")
    
    st.divider()
    
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Recent Queries")
        st.dataframe(queries_df[['timestamp', 'location', 'budget', 'num_recommendations']].tail(5))
    
    with colB:
        st.subheader("Recent Feedback")
        st.dataframe(feedback_df[['timestamp', 'restaurant_name', 'feedback_type']].tail(5))
