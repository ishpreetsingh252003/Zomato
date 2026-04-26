import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import os

st.set_page_config(page_title="Zomato AI - Phase 6 Analytics", layout="wide")

_DB_PATH = Path(__file__).resolve().parent.parent / "analytics.db"

def get_connection():
    if not _DB_PATH.exists():
        st.error(f"Database not found at {_DB_PATH}. Please run the Phase 6 backend and submit a query first.")
        st.stop()
    return sqlite3.connect(str(_DB_PATH))

st.title("📊 Zomato AI Recommendation Analytics")
st.markdown("Phase 6: Monitoring and Continuous Improvement Dashboard")

# -------------------------------------------------------------------------
# Load Data
# -------------------------------------------------------------------------
try:
    conn = get_connection()
    queries_df = pd.read_sql("SELECT * FROM queries", conn)
    feedback_df = pd.read_sql("SELECT * FROM feedback", conn)
    conn.close()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if queries_df.empty:
    st.info("No queries logged yet. Go to the Zomato AI app and get some recommendations!")
    st.stop()

# -------------------------------------------------------------------------
# Overview Metrics
# -------------------------------------------------------------------------
total_queries = len(queries_df)
avg_latency = queries_df['latency_ms'].mean() / 1000.0  # seconds

total_feedback = len(feedback_df)
likes = len(feedback_df[feedback_df['feedback_type'] == 'like'])
dislikes = len(feedback_df[feedback_df['feedback_type'] == 'dislike'])
like_ratio = (likes / total_feedback * 100) if total_feedback > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Queries", total_queries)
col2.metric("Avg Latency (s)", f"{avg_latency:.2f}s")
col3.metric("Total Feedback", total_feedback)
col4.metric("Like Ratio", f"{like_ratio:.1f}%")

st.divider()

# -------------------------------------------------------------------------
# Visualizations
# -------------------------------------------------------------------------
st.header("Trends")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Queries over time")
    if not queries_df.empty:
        # Group by hour
        queries_df['timestamp'] = pd.to_datetime(queries_df['timestamp'])
        hourly_queries = queries_df.groupby(queries_df['timestamp'].dt.floor('h')).size().reset_index(name='count')
        st.line_chart(hourly_queries.set_index('timestamp'))

with col2:
    st.subheader("Feedback Ratio")
    if not feedback_df.empty:
        feedback_counts = feedback_df['feedback_type'].value_counts()
        st.bar_chart(feedback_counts)

st.divider()

# -------------------------------------------------------------------------
# Problematic Queries (Dislikes)
# -------------------------------------------------------------------------
st.header("Problematic Recommendations (Needs Improvement)")
st.markdown("These recommendations received negative feedback. Use this to tune Phase 3 filtering or Phase 4 prompts.")

if dislikes > 0:
    disliked_recs = feedback_df[feedback_df['feedback_type'] == 'dislike']
    # Join with queries to see what the user asked for
    merged = pd.merge(disliked_recs, queries_df, on="query_id", how="left")
    
    display_df = merged[['timestamp_x', 'location', 'budget', 'cuisines', 'restaurant_name']]
    display_df.columns = ['Time', 'Location', 'Budget', 'Cuisines Requested', 'Restaurant (Disliked)']
    
    st.dataframe(display_df, use_container_width=True)
else:
    st.success("No dislikes recorded yet! 🎉")

st.divider()

# -------------------------------------------------------------------------
# Recent Queries
# -------------------------------------------------------------------------
st.header("Recent Queries")
st.dataframe(queries_df.sort_values(by='timestamp', ascending=False).head(10), use_container_width=True)
