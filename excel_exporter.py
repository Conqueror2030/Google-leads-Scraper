import pandas as pd
import os
import json

EXCEL_FILE = "lead_generation_matrix.xlsx"

def export_leads(leads: list):
    """
    Exports a list of lead dictionaries to Excel.
    Sorts strictly by Conversion Velocity Score (ascending) to place
    lowest scoring businesses at the top.

    Expected column order:
    ['Company Name', 'Website URL', 'Audited URL Bundle', 'Lead Contact Email', 'Phone Number', 'Is Running Ads', 'Google Rating', 'Conversion Velocity Score', 'What They Are Missing', 'Revenue Bleed Impact', 'Personalized Pitch Hook']
    """
    if not leads:
        print("No leads to export.")
        return

    df = pd.DataFrame(leads)

    # Enforce column order
    expected_columns = ['Company Name', 'Website URL', 'Audited URL Bundle', 'Lead Contact Email', 'Phone Number', 'Is Running Ads', 'Google Rating', 'Conversion Velocity Score', 'What They Are Missing', 'Revenue Bleed Impact', 'Personalized Pitch Hook']
    # Filter only columns that exist (in case of malformed data) but maintain order
    ordered_columns = [col for col in expected_columns if col in df.columns]
    df = df[ordered_columns]

    # Sort by Conversion Velocity Score ascending
    if 'Conversion Velocity Score' in df.columns:
        df = df.sort_values(by='Conversion Velocity Score', ascending=True)

    # Write to Excel
    try:
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        print(f"Successfully exported {len(leads)} leads to {EXCEL_FILE}")
    except Exception as e:
        print(f"Failed to export to Excel: {e}")

if __name__ == "__main__":
    # Test export
    dummy_leads = [
        {"Company Name": "A", "Website URL": "a.com", "Lead Contact Email": "a@a.com", "Conversion Velocity Score": 80, "What They Are Missing": "chat", "Revenue Bleed Impact": "High", "Personalized Pitch Hook": "hi"},
        {"Company Name": "B", "Website URL": "b.com", "Lead Contact Email": "b@b.com", "Conversion Velocity Score": 30, "What They Are Missing": "mobile", "Revenue Bleed Impact": "Low", "Personalized Pitch Hook": "hello"},
    ]
    export_leads(dummy_leads)
