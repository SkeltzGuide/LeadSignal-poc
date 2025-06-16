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

def timetohire_parser(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    vacancies = []
    cards = soup.select("div.VacatureList__Wrapper__Mk_7J")

    for card in cards:
        # Title
        title_tag = card.select_one("h3.VacatureList__Title__u4746")
        title = title_tag.get_text(strip=True) if title_tag else "No title"

        # URL
        link_tag = card.select_one("a.VacatureList__LinkBtn__3_4n3")
        href = link_tag.get("href") if link_tag else "#"
        url = href if href.startswith("http") else base_url.rstrip("/") + href

        # Description
        desc_tag = card.select_one("div.VacatureList__Content__mfD1j p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        vacancies.append({
            "company": "TTH",
            "source": "job_board",
            "title": title,
            "url": url,
            "description": description
        })

    return vacancies


# Hashing
def generate_job_hash(job: Dict) -> str:
    """Create a unique hash for a job entry."""
    data = f"{job['company']}{job['source']}{job['title']}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "jobs.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE,
            title TEXT,
            url TEXT,
            description TEXT,
            company TEXT,
            source TEXT,
            first_seen TEXT,
            last_seen TEXT,
            is_active INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def store_jobs(jobs: List[Dict]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    seen_hashes = set()

    for job in jobs:
        job_hash = generate_job_hash(job)
        seen_hashes.add(job_hash)

        cursor.execute("SELECT id FROM jobs WHERE hash = ?", (job_hash,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("""
                UPDATE jobs SET last_seen = ?, is_active = 1 WHERE hash = ?
            """, (now, job_hash))
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (
                    hash, title, url, description,
                    company, source,
                    first_seen, last_seen, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                job_hash,
                job['title'],
                job['url'],
                job['description'],
                job.get('company', 'Unknown'),
                job.get('source', 'Unknown'),
                now,
                now
            ))

    # Flag missing jobs as inactive
    cursor.execute("SELECT hash FROM jobs WHERE is_active = 1")
    all_active = cursor.fetchall()
    for (existing_hash,) in all_active:
        if existing_hash not in seen_hashes:
            cursor.execute("UPDATE jobs SET is_active = 0 WHERE hash = ?", (existing_hash,))

    conn.commit()
    conn.close()

def detect_job_changes(current_jobs: List[Dict]) -> Dict[str, List[Dict]]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Track what's seen this round
    seen_urls = set()
    new_jobs = []
    changed_jobs = []

    for job in current_jobs:
        job_hash = generate_job_hash(job)
        url = job['url']
        seen_urls.add(url)

        cursor.execute("SELECT hash FROM jobs WHERE url = ?", (url,))
        row = cursor.fetchone()

        if row:
            db_hash = row[0]
            if db_hash != job_hash:
                # Content changed → update hash and mark as changed
                job["status"] = "changed"
                changed_jobs.append(job)
                cursor.execute("""
                    UPDATE jobs
                    SET hash = ?, title = ?, description = ?, last_seen = ?, is_active = 1
                    WHERE url = ?
                """, (job_hash, job['title'], job['description'], now, url))
            else:
                # Just update last_seen
                cursor.execute("""
                    UPDATE jobs SET last_seen = ?, is_active = 1 WHERE url = ?
                """, (now, url))
        else:
            # New job
            job["status"] = "new"
            new_jobs.append(job)
            cursor.execute("""
                INSERT INTO jobs (
                    hash, title, url, description,
                    company, source,
                    first_seen, last_seen, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                job_hash,
                job['title'],
                url,
                job['description'],
                job.get('company', 'Unknown'),
                job.get('source', 'Unknown'),
                now,
                now
            ))

    # Detect removed jobs (active jobs not in current scrape)
    cursor.execute("SELECT url FROM jobs WHERE is_active = 1")
    all_active = {row[0] for row in cursor.fetchall()}

    removed_urls = all_active - seen_urls
    removed_jobs = []

    for url in removed_urls:
        removed_jobs.append({"url": url, "status": "removed"})
        cursor.execute("""
            UPDATE jobs SET is_active = 0 WHERE url = ?
        """, (url,))

    conn.commit()
    conn.close()

    return {
        "new": new_jobs,
        "changed": changed_jobs,
        "removed": removed_jobs
    }