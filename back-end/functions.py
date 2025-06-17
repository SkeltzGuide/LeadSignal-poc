# Imports
# Scraping
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

# Hashing
import hashlib

# Database
import sqlite3
from datetime import datetime
from typing import List, Dict
import os

# Functions
# Scraping
def scrape_target_site(
    site_name: str,
    base_url: str,
) -> List[Dict]:
    headers = {
        "User-Agent": f"LeadSignalBot/0.1 (+{site_name})"
    }

    response = requests.get(base_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


# Hashing
def generate_data_hash(data: Dict) -> str:
    """Create a unique hash for a data point."""
    to_hash = f"{data['project']}{data['type']}{data['name']}"
    return hashlib.sha256(to_hash.encode("utf-8")).hexdigest()

# Go up one level from back-end/ and into DB/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "..", "DB", "intent_data.db")
DB_NAME = os.path.abspath(DB_NAME)  # Normalize to absolute path

def init_db():
    print("🚧 Connecting to DB at:", DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intent_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE,
            name TEXT,
            url TEXT,
            description TEXT,
            project TEXT,
            type TEXT,
            first_seen TEXT,
            last_seen TEXT,
            is_active INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def store_data(updates: List[Dict]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    seen_hashes = set()

    for data in updates:
        data_hash = generate_data_hash(data)

        #print(job_hash, '<- job hash')

        seen_hashes.add(data_hash)

        cursor.execute("SELECT id FROM intent_data WHERE hash = ?", (data_hash,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("""
                UPDATE intent_data SET last_seen = ?, is_active = 1 WHERE hash = ?
            """, (now, data_hash))
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO intent_data (
                    hash, name, url, description,
                    project, type,
                    first_seen, last_seen, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data_hash,
                data['name'],
                data['url'],
                data['description'],
                data.get('project', 'Unknown'),
                data.get('type', 'Unknown'),
                now,
                now
            ))

    # Flag missing updates as inactive
    cursor.execute("SELECT hash FROM intent_data WHERE is_active = 1")
    all_active = cursor.fetchall()
    for (existing_hash,) in all_active:
        if existing_hash not in seen_hashes:
            cursor.execute("UPDATE intent_data SET is_active = 0 WHERE hash = ?", (existing_hash,))

    conn.commit()
    conn.close()

def detect_changes(current_data: List[Dict]) -> Dict[str, List[Dict]]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Track what's seen this round
    seen_urls = set()
    new_updates = []
    changed_updates = []
    
    print("number of data: ", len(current_data))
    for data in current_data:
        data_hash = generate_data_hash(data)

        print("\n")
        print('data & hash: ', data, data_hash)
        url = data['url']
        seen_urls.add(url)

        cursor.execute("SELECT hash FROM intent_data WHERE url = ?", (url,))
        row = cursor.fetchone()

        print('content of db with that hash:', data_hash, row)

        if row:
            print('yes row')
            db_hash = row[0]
            print('content of db: ', db_hash)
            if db_hash != data_hash:
                # Content changed → update hash and mark as changed
                data["status"] = "changed"
                changed_updates.append(data)
                cursor.execute("""
                    UPDATE intent_data
                    SET hash = ?, name = ?, description = ?, last_seen = ?, is_active = 1
                    WHERE url = ?
                """, (data_hash, data['name'], data['description'], now, url))
            else:
                # Just update last_seen
                cursor.execute("""
                    UPDATE intent_data SET last_seen = ?, is_active = 1 WHERE url = ?
                """, (now, url))
        else:
            print('no row')
            # New job
            data["status"] = "new"
            new_updates.append(data)
            cursor.execute("""
                INSERT INTO intent_data (
                    hash, name, url, description,
                    project, type,
                    first_seen, last_seen, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data_hash,
                data['name'],
                url,
                data['description'],
                data.get('project', 'Unknown'),
                data.get('type', 'Unknown'),
                now,
                now
            ))

    # Detect removed jobs (active jobs not in current scrape)
    cursor.execute("SELECT url FROM intent_data WHERE is_active = 1")
    all_active = {row[0] for row in cursor.fetchall()}

    removed_urls = all_active - seen_urls
    removed_updates = []

    for url in removed_urls:
        removed_updates.append({"url": url, "status": "removed"})
        cursor.execute("""
            UPDATE intent_data SET is_active = 0 WHERE url = ?
        """, (url,))

    conn.commit()
    conn.close()

    return {
        "new": new_updates,
        "changed": changed_updates,
        "removed": removed_updates
    }