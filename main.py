import time
import json
import simdjson
from brainstormer import get_target_niches
from maps_scraper import get_business_domains
from dropdown_finder import get_dropdown_links
from cache_manager import check_cache, save_to_cache
from gemini_auditor import audit_business, RateLimitError
from excel_exporter import export_leads

def run_pipeline(offering: str, city: str = "New York"):
    print(f"Starting pipeline for offering: {offering} in {city}")

    # 1. Brainstorm Targets
    print("Brainstorming niches...")
    brainstorm_data = get_target_niches(offering)
    targets = brainstorm_data.get("target_leads", [])

    if not targets:
        print("Failed to brainstorm targets. Exiting.")
        return

    all_leads = []

    # 2. Iterate over targets
    for target in targets:
        niche = target["niche"]
        query = target["search_query"]
        print(f"\n--- Processing Niche: {niche} (Query: {query}) ---")

        # Scrape Base Domains
        domains = get_business_domains(query, city=city)
        print(f"Found {len(domains)} domains for {niche}.")

        for domain in domains:
            print(f"Evaluating: {domain}")

            # Check Cache
            cached_data = check_cache(domain)
            if cached_data:
                print(f"Cache HIT for {domain}. Skipping API.")
                lead_entry = {
                    "niche": niche,
                    "search_query": query,
                    "domain": domain,
                    "cvs_score": cached_data["cvs_score"],
                    "flaw_data": cached_data["flaw_data"],
                    "pitch_email": cached_data["pitch_email"]
                }
                all_leads.append(lead_entry)
                continue

            print(f"Cache MISS for {domain}. Proceeding with live audit.")

            # Extract Dropdowns
            sub_links = get_dropdown_links(domain)
            urls_to_audit = [domain] + sub_links
            print(f"Bundled {len(urls_to_audit)} URLs for audit.")

            # Audit via Gemini
            try:
                # This could fail if API key is invalid or structured output parsing fails entirely
                # The tenacity retry handles 429s internally
                audit_result_str = audit_business(urls_to_audit)
                audit_result = simdjson.loads(audit_result_str)

                cvs_score = audit_result.get("conversion_velocity_score", 100)
                flaw_data = audit_result.get("flaw_data", [])
                pitch_email = audit_result.get("pitch_email", "")

                # Save to cache
                save_to_cache(domain, cvs_score, flaw_data, pitch_email)

                lead_entry = {
                    "niche": niche,
                    "search_query": query,
                    "domain": domain,
                    "cvs_score": cvs_score,
                    "flaw_data": flaw_data,
                    "pitch_email": pitch_email
                }
                all_leads.append(lead_entry)

            except json.JSONDecodeError:
                print(f"Error: Gemini returned invalid JSON for {domain}.")
            except RateLimitError as e:
                print(f"Error: Rate limit exhausted for {domain}: {e}")
            except Exception as e:
                print(f"Error auditing {domain}: {e}")

            # Mandatory Global Throttle to protect 10 RPM quota
            print("Sleeping for 6 seconds to respect global quota limits...")
            time.sleep(6)

    # 3. Export
    if all_leads:
        print("\nExporting all leads...")
        export_leads(all_leads)
    else:
        print("\nNo leads to export.")

if __name__ == "__main__":
    run_pipeline("Premium Website & AI Chatbot Development")
