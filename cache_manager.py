import sqlite3
import json

DB_FILE = "cache.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audited_leads (
            domain TEXT PRIMARY KEY,
            cvs_score INTEGER,
            flaw_data TEXT,
            pitch_email TEXT
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
    cursor.execute("SELECT cvs_score, flaw_data, pitch_email FROM audited_leads WHERE domain = ?", (domain,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "cvs_score": result[0],
            "flaw_data": json.loads(result[1]),
            "pitch_email": result[2]
        }
    return None

def save_to_cache(domain: str, cvs_score: int, flaw_data: list, pitch_email: str):
    """
    Saves the audit results to the SQLite cache.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    flaw_data_json = json.dumps(flaw_data)
    cursor.execute(
        "INSERT OR REPLACE INTO audited_leads (domain, cvs_score, flaw_data, pitch_email) VALUES (?, ?, ?, ?)",
        (domain, cvs_score, flaw_data_json, pitch_email)
    )
    conn.commit()
    conn.close()

# Initialize the database on module load
init_db()
