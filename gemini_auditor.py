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
def audit_business(urls: List[str]) -> dict:
    """
    Audits a list of bundled URLs (Homepage + Dropdown service pages).
    Uses v1beta1 API and url_context tool to evaluate CVS score.
    Retries on errors (specifically targeting 429).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable is missing. Auditor may fail.")

    # Initialize client specifically with v1beta1 to use url_context
    client = genai.Client(http_options={"api_version": "v1beta1"})

    # Format the URLs as the contents of the prompt
    url_list_str = "\n".join(urls)

    prompt = f"""
    Please audit the following website URLs for a local business:
    {url_list_str}

    Evaluate the full live web context under the standard Conversion Velocity Score (CVS) metric.
    Start at 100 points and deduct value mathematically based on the following criteria:
    - Deduct 40 points if the site completely lacks an interactive conversational assistant or 24/7 instant booking mechanism.
    - Deduct 30 points if visual structures present bad mobile viewports, unappealing color contrast, or hidden CTAs.
    - Deduct 20 points if high-ticket service sub-pages contain blocks of text without localized capture funnels.
    - Deduct 10 points if resource loading indicates broken asset files or bloated code structure.

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

if __name__ == "__main__":
    # Dummy test to verify syntax and retry logic structure
    pass
