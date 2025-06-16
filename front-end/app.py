import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "jobs.db"

def load_changes():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT title, url, company, source, first_seen, last_seen, is_active
        FROM jobs
        ORDER BY last_seen DESC
        LIMIT 100
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    now = datetime.utcnow().isoformat()
    df["status"] = df.apply(lambda row: detect_status(row), axis=1)
    return df

def detect_status(row):
    if row["is_active"] == 0:
        return "❌ Removed"
    elif row["first_seen"] == row["last_seen"]:
        return "🆕 New"
    elif row["first_seen"] != row["last_seen"]:
        return "♻️ Changed"
    return ""

# --- Streamlit UI ---

st.title("📡 LeadSignal Notifications")
st.caption("Live updates on monitored job listings")

df = load_changes()

if df.empty:
    st.info("No job listings to show yet.")
else:
    for _, row in df.iterrows():
        st.markdown(f"""
        {row['status']} **{row['title']}**  
        🔗 [View Job]({row['url']})  
        🏢 {row['company']} | 🧠 Source: {row['source']}  
        🕒 Last Seen: `{row['last_seen']}`
        ---
        """)

st.button("🔄 Refresh")
