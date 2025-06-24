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

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT id, name, url, project, resource, type, first_seen, last_seen, is_active
        FROM intent_data
        ORDER BY last_seen ASC
        LIMIT 25
    """, conn)
    conn.close()
    df["status"] = df.apply(lambda row: classify_first_seen(row), axis=1)
    return df
    
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
    
def get_ai_insight():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT id, priority, reasoning, action
        FROM ai_insights
    """, conn)
    conn.close()
    return df

df = get_data()
ins = get_ai_insight()

projects = df['project'].unique()

# --- Sidebar: Project selection ---
selected_project = st.sidebar.selectbox("Select Project", projects)

# Filter DataFrame for the selected project
project_df = df[df['project'] == selected_project]

# Get unique resource types for tabs
resources = project_df['resource'].unique().tolist()
tabs = st.tabs(resources)

for tab, resource in zip(tabs, resources):
    with tab:
        filtered_df = project_df[project_df['resource'] == resource]

        for _, row in filtered_df.iloc[::-1].iterrows():
            
            # pre-generate AI information
            ai_data = ins[ins['id'] == row['id']].iloc[0]
            priority = ai_data['priority'].lower()
            reasoning = ai_data['reasoning']
            action = ai_data['action']

            # Color coding for priority
            priority_color = {
                'low': '#34a853',     # green
                'medium': '#fbbc05',  # orange
                'high': '#ea4335'     # red
            }.get(priority, '#888')

            # Check for "New"
            try:
                first_seen = datetime.fromisoformat(row["first_seen"])
                is_new = (datetime.utcnow() - first_seen) < timedelta(seconds=60)
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
                        <div style="font-size:17px; font-weight:600; color:#333; margin-bottom:6px;">
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
                                <div style="margin-top:6px;">
                                <strong>Priority:</strong>
                                <span style="color:{priority_color}; font-weight:600;">{priority.capitalize()}</span>
                            </div>
                            <div style="margin-top:4px;">
                                <strong>Reasoning:</strong> {reasoning}
                            </div>
                            <div style="margin-top:4px; font-style: italic; color:#555;">
                                <strong>Suggested Action:</strong> {action}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)



# Sleep and rerun
time.sleep(15)
st.rerun()
