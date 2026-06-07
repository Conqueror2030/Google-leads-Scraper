import pandas as pd
import os
import json

EXCEL_FILE = "lead_generation_matrix.xlsx"

def export_leads(leads: list):
    """
    Exports a list of lead dictionaries to Excel.
    Sorts strictly by conversion_velocity_score (ascending) to place
    lowest scoring businesses at the top.

    Expected lead format:
    {
        "niche": "...",
        "search_query": "...",
        "domain": "...",
        "cvs_score": int,
        "flaw_data": ["..."],
        "pitch_email": "..."
    }
    """
    if not leads:
        print("No leads to export.")
        return

    df = pd.DataFrame(leads)

    # Sort by conversion velocity score ascending
    if 'cvs_score' in df.columns:
        df = df.sort_values(by='cvs_score', ascending=True)

    # Convert lists to strings for Excel compatibility
    if 'flaw_data' in df.columns:
        df['flaw_data'] = df['flaw_data'].apply(lambda x: "\n".join(x) if isinstance(x, list) else x)

    # Write to Excel
    try:
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        print(f"Successfully exported {len(leads)} leads to {EXCEL_FILE}")
    except Exception as e:
        print(f"Failed to export to Excel: {e}")

if __name__ == "__main__":
    # Test export
    dummy_leads = [
        {"niche": "Roofing", "search_query": "roofers", "domain": "a.com", "cvs_score": 80, "flaw_data": ["no chat"], "pitch_email": "hi"},
        {"niche": "Roofing", "search_query": "roofers", "domain": "b.com", "cvs_score": 30, "flaw_data": ["no chat", "bad mobile"], "pitch_email": "hello"},
    ]
    export_leads(dummy_leads)
