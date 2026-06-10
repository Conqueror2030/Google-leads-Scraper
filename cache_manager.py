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
            business_name TEXT,
            cvs_score INTEGER,
            what_they_are_missing TEXT,
            revenue_bleed_impact TEXT,
            personalized_pitch_hook TEXT,
            extracted_email TEXT,
            audited_bundle TEXT
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
    cursor.execute("SELECT business_name, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, extracted_email, audited_bundle FROM audited_leads WHERE domain = ?", (domain,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "business_name": result[0],
            "cvs_score": result[1],
            "what_they_are_missing": result[2],
            "revenue_bleed_impact": result[3],
            "personalized_pitch_hook": result[4],
            "extracted_email": result[5],
            "audited_bundle": result[6]
        }
    return None

def save_to_cache(domain: str, business_name: str, cvs_score: int, what_they_are_missing: str, revenue_bleed_impact: str, personalized_pitch_hook: str, extracted_email: str, audited_bundle: str):
    """
    Saves the audit results to the SQLite cache.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO audited_leads (domain, business_name, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, extracted_email, audited_bundle) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (domain, business_name, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, extracted_email, audited_bundle)
    )
    conn.commit()
    conn.close()

# Initialize the database on module load
init_db()
