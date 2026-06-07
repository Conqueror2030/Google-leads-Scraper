import sqlite3
import json
import simdjson

DB_FILE = "cache.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audited_leads (
            domain TEXT PRIMARY KEY,
            cvs_score INTEGER,
            what_they_are_missing TEXT,
            revenue_bleed_impact TEXT,
            personalized_pitch_hook TEXT,
            extracted_email TEXT
        )
    ''')
    conn.commit()
    conn.close()

def check_cache(domain: str):
    """
    Returns a dictionary of cached data if the domain exists in the cache, otherwise None.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, extracted_email FROM audited_leads WHERE domain = ?", (domain,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "cvs_score": result[0],
            "what_they_are_missing": result[1],
            "revenue_bleed_impact": result[2],
            "personalized_pitch_hook": result[3],
            "extracted_email": result[4]
        }
    return None

def save_to_cache(domain: str, cvs_score: int, what_they_are_missing: str, revenue_bleed_impact: str, personalized_pitch_hook: str, extracted_email: str):
    """
    Saves the audit results to the SQLite cache.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO audited_leads (domain, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, extracted_email) VALUES (?, ?, ?, ?, ?, ?)",
        (domain, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, extracted_email)
    )
    conn.commit()
    conn.close()

# Initialize the database on module load
init_db()
