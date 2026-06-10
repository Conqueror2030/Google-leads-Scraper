import os
from google import genai
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import List

class AuditResult(BaseModel):
    conversion_velocity_score: int
    what_they_are_missing: str
    revenue_bleed_impact: str
    personalized_pitch_hook: str

# Define exception type for Tenacity to catch.
# Depending on the exact exception google.genai throws for 429, we might just catch Exception
# However, usually there's an APIError.
class RateLimitError(Exception):
    pass

def check_for_429(e: Exception) -> bool:
    # A simple way to check if an exception is related to 429
    return "429" in str(e)

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"Retrying auditor due to error: {retry_state.outcome.exception()}..."),
    reraise=True
)
def audit_business(urls: List[str], is_spending_on_ads: bool = False) -> dict:
    """
    Audits a list of bundled URLs (Homepage + Dropdown service pages).
    Uses standard API and url_context tool to evaluate CVS score.
    Tailors the revenue bleed and pitch if the business is actively spending on ads.
    Retries on errors (specifically targeting 429).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable is missing. Auditor may fail.")

    client = genai.Client()

    # Format the URLs as the contents of the prompt
    url_list_str = "\n".join(urls)

    ad_waste_directive = ""
    if is_spending_on_ads:
        ad_waste_directive = """
    CRITICAL: This business is currently flagged with 'IS_SPENDING_ON_ADS: True'.
    You must run a strict comparative analysis to verify if their high-ticket service dropdown landing pages are missing conversational assistants or 24/7 capture funnels.
    Map this directly to the 'revenue_bleed_impact' output focusing entirely on ad budget waste.
    Explicitly weave mentions of their unique dropdown services by name and their ad leakage into the generated 'personalized_pitch_hook' email template.
    """

    prompt = f"""
    You are an expert Conversion Rate Optimization auditor.
    Analyze the entire digital footprint provided in this multi-URL cloud context bundle simultaneously:

    {url_list_str}

    Cross-examine the structural layouts, text placement, and asset files.

    Evaluate the full context under the standard Conversion Velocity Score (CVS) metric.
    Start at 100 points and deduct value mathematically based on the following criteria:
    - Deduct 40 points if the site completely lacks an interactive conversational assistant or 24/7 instant booking mechanism.
    - Deduct 30 points if visual structures present bad mobile viewports, unappealing color contrast, or hidden CTAs.
    - Deduct 20 points if high-ticket service sub-pages contain blocks of text without localized capture funnels.
    - Deduct 10 points if resource loading indicates broken asset files or bloated code structure.

    {ad_waste_directive}

    If 'IS_SPENDING_ON_ADS: True' is not flagged, still ensure you explicitly weave mentions of their unique dropdown services by name into the 'personalized_pitch_hook' email template.

    Return the result strictly as a JSON object matching this schema:
    - conversion_velocity_score: integer (the calculated score, 0 to 100)
    - what_they_are_missing: string (Explicit visual or conversational features completely lacking on the site)
    - revenue_bleed_impact: string (A calculated mathematical reason showing the business owner exactly how much traffic/capital they are actively losing due to these flaws)
    - personalized_pitch_hook: string (A 100% customized cold outreach email targeting their specific dropdown services by name)
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "tools": [{"url_context": {}}],
                "response_mime_type": "application/json",
                "response_schema": AuditResult,
            },
        )
        return response.text # Pydantic schema enforces JSON output from Gemini
    except Exception as e:
        if check_for_429(e):
            raise RateLimitError(str(e)) # Raise specific error for retry mechanism
        raise e

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"Retrying missing website auditor due to error: {retry_state.outcome.exception()}..."),
    reraise=True
)
def audit_missing_website(business_name: str, is_spending_on_ads: bool = False) -> dict:
    """
    Handles businesses completely missing a website footprint.
    Does NOT use the url_context tool. Forces score to 0.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable is missing. Auditor may fail.")

    client = genai.Client() # Standard client, no v1beta1 required here

    ad_waste_directive = ""
    if is_spending_on_ads:
        ad_waste_directive = """
    CRITICAL: This business is currently SPENDING MONEY ON ADS, but has NO website!
    You must construct the 'revenue_bleed_impact' analysis explicitly highlighting the extreme waste of paying for ads when prospective clients have nowhere digital to land or book.
    Weave a direct mention of this active ad leakage into the 'personalized_pitch_hook' to grab their attention.
    """

    prompt = f"""
    The local business "{business_name}" is completely lacking a website or digital footprint.

    {ad_waste_directive}

    Evaluate this business and return the result strictly as a JSON object matching this schema:
    - conversion_velocity_score: Must be strictly set to the integer 0.
    - what_they_are_missing: string (Explicitly state they lack a digital footprint and online booking capability)
    - revenue_bleed_impact: string (Calculate the mathematical reason showing the owner how much traffic/capital they are actively losing due to zero digital presence)
    - personalized_pitch_hook: string (A high-converting customized cold outreach email offering a rapid premium website and chatbot package build)
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": AuditResult,
            },
        )
        return response.text
    except Exception as e:
        if check_for_429(e):
            raise RateLimitError(str(e))
        raise e

if __name__ == "__main__":
    # Dummy test to verify syntax and retry logic structure
    pass
