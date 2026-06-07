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

        # Scrape Businesses
        businesses = get_business_domains(query, city=city)
        print(f"Found {len(businesses)} businesses for {niche}.")

        for business in businesses:
            domain = business.get("root_url")
            business_name = business.get("business_name", "Unknown Business")
            is_spending_on_ads = business.get("is_spending_on_ads", False)

            if not domain:
                continue

            print(f"Evaluating: {business_name} ({domain}) | Ads Active: {is_spending_on_ads}")

            # Check Cache
            cached_data = check_cache(domain)
            if cached_data:
                print(f"Cache HIT for {domain}. Skipping API.")
                lead_entry = {
                    "Company Name": cached_data.get("business_name", business_name),
                    "Website URL": domain,
                    "Lead Contact Email": cached_data.get("extracted_email", "No email found"),
                    "Conversion Velocity Score": cached_data["cvs_score"],
                    "What They Are Missing": cached_data["what_they_are_missing"],
                    "Revenue Bleed Impact": cached_data["revenue_bleed_impact"],
                    "Personalized Pitch Hook": cached_data["personalized_pitch_hook"]
                }
                all_leads.append(lead_entry)
                continue

            print(f"Cache MISS for {domain}. Proceeding with live audit.")

            # Extract Dropdowns and Emails
            dropdown_data = get_dropdown_links(domain)
            sub_links = dropdown_data.get("links", [])
            extracted_emails = dropdown_data.get("emails", [])
            primary_email = extracted_emails[0] if extracted_emails else "No email found"

            urls_to_audit = [domain] + sub_links
            print(f"Bundled {len(urls_to_audit)} URLs for audit. Found email: {primary_email}")

            # Audit via Gemini
            try:
                # This could fail if API key is invalid or structured output parsing fails entirely
                # The tenacity retry handles 429s internally
                audit_result_str = audit_business(urls_to_audit, is_spending_on_ads=is_spending_on_ads)
                audit_result = simdjson.loads(audit_result_str)

                cvs_score = audit_result.get("conversion_velocity_score", 100)
                what_they_are_missing = audit_result.get("what_they_are_missing", "")
                revenue_bleed_impact = audit_result.get("revenue_bleed_impact", "")
                personalized_pitch_hook = audit_result.get("personalized_pitch_hook", "")

                # Save to cache
                save_to_cache(domain, business_name, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, primary_email)

                lead_entry = {
                    "Company Name": business_name,
                    "Website URL": domain,
                    "Lead Contact Email": primary_email,
                    "Conversion Velocity Score": cvs_score,
                    "What They Are Missing": what_they_are_missing,
                    "Revenue Bleed Impact": revenue_bleed_impact,
                    "Personalized Pitch Hook": personalized_pitch_hook
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
