import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta

import os

# Correct DB connection
# Path to ../DB/jobs.db relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.abspath(os.path.join(BASE_DIR, "..", "DB", "intent_data.db"))

# Optional: print to verify
print("📂 Connecting to DB at:", DB_NAME)

# Visual User Interface
# Refresh every 15 seconds
st.title("📡 LeadSignal Monitor")
st.caption("Auto-refreshing every 15 seconds to show notifications on data source changes.")

# Hide "Running..." warning
st.markdown("""
    <style>
        [data-testid="stStatusWidget"] { display: none; }
    </style>
""", unsafe_allow_html=True)

def get_changes():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT name, url, project, type, first_seen, last_seen, is_active
        FROM intent_data
        ORDER BY last_seen ASC
        LIMIT 25
    """, conn)
    conn.close()
    df["status"] = df.apply(lambda row: classify_first_seen(row), axis=1)
    return df

def detect_status(row):
    if row["is_active"] == 0:
        return "❌ Removed"
    elif row["first_seen"] == row["last_seen"]:
        return "🆕 New"
    else:
        return "♻️ Changed"
    
def classify_first_seen(row):
    try:
        first_seen = datetime.fromisoformat(row['first_seen'])
        now = datetime.utcnow()
        if (now - first_seen) < timedelta(seconds=30):
            return "new"
        else:
            return "old"
    except Exception as e:
        return f"error: {e}"

df = get_changes()



projects = df['project'].unique()
tabs = st.tabs([f"🏢 {project}" for project in projects])

for tab, project in zip(tabs, projects):
    with tab:
        project_df = df[df['project'] == project]

        for _, row in project_df.iloc[::-1].iterrows():
            # Check for "New"
            try:
                first_seen = datetime.fromisoformat(row["first_seen"])
                is_new = (datetime.utcnow() - first_seen) < timedelta(seconds=30)
            except:
                is_new = False

            badge = '<span style="color:#e53935; font-weight:bold;">🔴 New</span>' if is_new else ""

            with st.container():
                st.markdown(f"""
                    <div style="
                        background-color:#f0f4f8;
                        border-left: 4px solid #1a73e8;
                        padding:16px 20px 12px;
                        margin-bottom:24px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                        font-family: 'Segoe UI', sans-serif;
                        border-radius: 10px;
                    ">
                        <div style="font-size:17px; font-weight:600; margin-bottom:6px;">
                            {row['name']} {badge}
                        </div>
                        <div style="font-size:14px; color:#333; margin-bottom:6px;">
                            💡 {row['type']}<br>
                            🔗 <a href="{row['url']}" target="_blank" style="color:#1a73e8;">View Link</a>
                        </div>
                        <div style="font-size:12px; color:#666; margin-bottom:12px;">
                            🕒 Last Seen: {row['last_seen']}
                        </div>
                        <hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0;">
                        <div style="font-size:13px; color:#444;">
                            🧠 <strong>AI Insight:</strong><br>
                            This lead shows potential interest based on recent interactions. Add custom insights here.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)



# Sleep and rerun
time.sleep(15)
st.rerun()
