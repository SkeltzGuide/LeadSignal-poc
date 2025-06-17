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
st.caption("Auto-refreshing every 15 seconds to show job change notifications.")

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

# Group by project
projects = df['project'].unique()

for project in projects:
    with st.expander(f"🏢 {project} ({len(df[df['project'] == project])} entries)", expanded=False):
        project_df = df[df['project'] == project]

    for _, row in project_df.iterrows():
        # Show badge only if status is "now"
        badge = '<span style="color:#2196f3; font-weight:bold;">🔵 New</span>' if row["status"] == "new" else ""

        st.markdown(f"""
        <div style="
            background-color:#f9f9f9;
            border-radius:10px;
            padding:14px 18px;
            margin-bottom:10px;
            box-shadow:0 1px 2px rgba(0,0,0,0.06);
            font-family:Arial, sans-serif;
        ">
            <div style="font-size:16px; font-weight:600; margin-bottom:6px;">
                {row['name']} {badge}
            </div>
            <div style="font-size:13px; color:#444;">
                🧠 {row['type']}
            </div>
            <div style="font-size:13px; margin:6px 0;">
                🔗 <a href="{row['url']}" target="_blank" style="color:#1a73e8;">View Job</a>
            </div>
            <div style="font-size:11px; color:#888;">
                🕒 Last Seen: {row['last_seen']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Sleep and rerun
time.sleep(15)
st.rerun()
