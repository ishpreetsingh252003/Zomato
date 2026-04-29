import streamlit as st
import sys
import pandas as pd
from pathlib import Path
import time
import os
import json

# --- STREAMLIT SECRETS (Cloud) + .env (Local) ---
# Streamlit Cloud doesn't have .env files; read API key from secrets instead.
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# --- PATH CONFIGURATION ---
_DEPLOY_DIR = Path(__file__).resolve().parent
_ARCH_DIR = _DEPLOY_DIR.parent
p6_backend_dir = str(_ARCH_DIR / "phase_6_monitoring" / "backend")
if p6_backend_dir not in sys.path:
    sys.path.insert(0, p6_backend_dir)

import orchestrator
import analytics_logger

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="Zomato AI Recommendations", layout="centered", page_icon="🍽️")

# --- CUSTOM CSS ---
st.markdown("""
<style>
div.stButton > button {
    border-radius: 20px;
    font-weight: 600;
    width: 100%;
    background-color: #e23744;
    color: white;
}
.stSlider [data-baseweb="slider"] {
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- LOAD METADATA DIRECTLY ---
def load_metadata():
    meta_p = _DEPLOY_DIR / "metadata.json"
    if meta_p.exists():
        try:
            return json.loads(meta_p.read_text(encoding="utf-8"))
        except:
            pass
    # Fallback to local import if possible, or defaults
    try:
        return orchestrator.get_metadata()
    except:
        return {
            "locations": ["Bangalore", "Indiranagar", "Koramangala", "HSR Layout", "Whitefield"], 
            "cuisines": ["Italian", "Chinese", "North Indian", "South Indian", "Cafe", "Desserts"]
        }

metadata = load_metadata()

# =========================================================================
# MAIN USER UI (Single Page)
# =========================================================================
st.title("🍽️ Zomato AI Recommendations")
st.markdown("Discover the best restaurants tailored specifically to your taste.")

with st.form("preference_form"):
    col1, col2 = st.columns(2)
    with col1:
        location = st.selectbox("📍 Select Location", metadata.get("locations", ["Bangalore"]))
        budget_raw = st.slider("💰 Budget for two (₹)", min_value=200, max_value=4000, value=1000, step=100)
    with col2:
        cuisines_selection = st.selectbox("🍜 Preferred Cuisine", ["Any"] + metadata.get("cuisines", []))
        min_rating = st.slider("⭐ Minimum Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    
    optional_prefs = st.text_input("✨ Special requirements (e.g. Rooftop, Family friendly)", "Quick service")
    top_n = st.selectbox("🏆 How many recommendations?", [3, 5, 10], index=1)
    
    submitted = st.form_submit_button("Get AI Recommendations")

if submitted:
    # Convert budget to categories expected by engine
    budget_str = "low" if budget_raw <= 600 else ("medium" if budget_raw <= 1500 else "high")
    cuisine_list = [] if cuisines_selection == "Any" else [cuisines_selection]
    opt_prefs_list = [p.strip() for p in optional_prefs.split(",") if p.strip()]
    
    preferences = {
        "location": location,
        "budget": budget_str,
        "cuisines": cuisine_list,
        "min_rating": min_rating,
        "optional_preferences": opt_prefs_list
    }
    
    with st.spinner("AI is analyzing restaurant data..."):
        start_time = time.time()
        try:
            result = orchestrator.run_pipeline(preferences, top_n=top_n)
            latency_ms = (time.time() - start_time) * 1000.0
            
            recs = result.get("recommendations", [])
            query_id = analytics_logger.log_query(preferences, len(recs), latency_ms)
            
            st.success(f"Found {len(recs)} great matches for you!")
            
            for rec in recs:
                with st.expander(f"**{rec['restaurant_name']}** — ⭐ {rec.get('rating', 'N/A')} — ₹{rec.get('cost_for_two', 'N/A')}", expanded=True):
                    st.markdown(f"**Cuisine:** {rec.get('cuisine', 'Multi-cuisine')}")
                    st.write(f"{rec.get('explanation', '')}")
                    
                    # Feedback Buttons
                    c1, c2, c3 = st.columns([1, 1, 4])
                    with c1:
                        if st.button("👍", key=f"l_{query_id}_{rec['rank']}"):
                            analytics_logger.log_feedback(query_id, rec['restaurant_name'], "like")
                            st.toast("Liked!")
                    with c2:
                        if st.button("👎", key=f"d_{query_id}_{rec['rank']}"):
                            analytics_logger.log_feedback(query_id, rec['restaurant_name'], "dislike")
                            st.toast("Disliked")
            
            st.caption(f"Powered by Groq LLM | Results from {result.get('source', 'engine')}")
                    
        except Exception as e:
            st.error("Something went wrong while processing your request. Please try again.")
            st.exception(e) # Useful for the user to see the exact error in this phase
