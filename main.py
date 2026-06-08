import time
import json
import simdjson
from brainstormer import get_target_niches
from maps_scraper import get_business_domains
from dropdown_finder import get_dropdown_links
from cache_manager import check_cache, save_to_cache
from gemini_auditor import audit_business, audit_missing_website, RateLimitError
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
            domain = business.get("root_url", "").strip()
            business_name = business.get("business_name", "Unknown Business")
            is_spending_on_ads = business.get("is_spending_on_ads", False)
            phone_number = business.get("phone_number", "")
            google_rating = business.get("google_rating", "")

            cache_key = domain if domain else f"NO_URL_{business_name.replace(' ', '_')}"
            display_url = domain if domain else "No Website"

            print(f"Evaluating: {business_name} ({display_url}) | Ads Active: {is_spending_on_ads}")

            # Check Cache
            cached_data = check_cache(cache_key)
            if cached_data:
                print(f"Cache HIT for {cache_key}. Skipping API.")
                lead_entry = {
                    "Company Name": cached_data.get("business_name", business_name),
                    "Website URL": display_url,
                    "Audited URL Bundle": cached_data.get("audited_bundle", "No Website"),
                    "Lead Contact Email": cached_data.get("extracted_email", "No email found"),
                    "Phone Number": phone_number,
                    "Is Running Ads": is_spending_on_ads,
                    "Google Rating": google_rating,
                    "Conversion Velocity Score": cached_data["cvs_score"],
                    "What They Are Missing": cached_data["what_they_are_missing"],
                    "Revenue Bleed Impact": cached_data["revenue_bleed_impact"],
                    "Personalized Pitch Hook": cached_data["personalized_pitch_hook"]
                }
                all_leads.append(lead_entry)
                continue

            print(f"Cache MISS for {cache_key}. Proceeding with live audit.")

            primary_email = "No email found"
            audited_bundle_str = "No Website"

            try:
                if not domain:
                    # Logic for Missing Website Footprint
                    print("Executing zero-score direct audit for missing website...")
                    audit_result_str = audit_missing_website(business_name, is_spending_on_ads=is_spending_on_ads)
                    audit_result = simdjson.loads(audit_result_str)
                else:
                    # Extract Dropdowns and Emails for Valid Domains
                    dropdown_data = get_dropdown_links(domain)
                    sub_links = dropdown_data.get("links", [])
                    extracted_emails = dropdown_data.get("emails", [])
                    if extracted_emails:
                        primary_email = extracted_emails[0]

                    urls_to_audit = [domain] + sub_links
                    audited_bundle_str = ", ".join(urls_to_audit)
                    print(f"Bundled {len(urls_to_audit)} URLs for audit. Found email: {primary_email}")

                    # Standard Audit via Gemini
                    audit_result_str = audit_business(urls_to_audit, is_spending_on_ads=is_spending_on_ads)
                    audit_result = simdjson.loads(audit_result_str)

                cvs_score = audit_result.get("conversion_velocity_score", 100 if domain else 0)
                what_they_are_missing = audit_result.get("what_they_are_missing", "")
                revenue_bleed_impact = audit_result.get("revenue_bleed_impact", "")
                personalized_pitch_hook = audit_result.get("personalized_pitch_hook", "")

                # Save to cache
                save_to_cache(cache_key, business_name, cvs_score, what_they_are_missing, revenue_bleed_impact, personalized_pitch_hook, primary_email, audited_bundle_str)

                lead_entry = {
                    "Company Name": business_name,
                    "Website URL": display_url,
                    "Audited URL Bundle": audited_bundle_str,
                    "Lead Contact Email": primary_email,
                    "Phone Number": phone_number,
                    "Is Running Ads": is_spending_on_ads,
                    "Google Rating": google_rating,
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
