import os
import json
from google import genai
from pydantic import BaseModel
from typing import List

class TargetLead(BaseModel):
    niche: str
    search_query: str

class BrainstormResult(BaseModel):
    target_leads: List[TargetLead]

def get_target_niches(offering_description: str) -> dict:
    """
    Uses Gemini to brainstorm top 3 highest-ticket local business niches and corresponding search queries.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable is missing. Brainstormer may fail.")

    client = genai.Client(http_options={"api_version": "v1"})

    prompt = f"""
    Given the following offering description: "{offering_description}"

    Brainstorm the top 3 highest-ticket local business niches that would benefit the most from this offering.
    For each niche, provide a high-intent Google Maps search query that a prospective client might use to find these businesses locally.

    Return the result strictly as a JSON object matching this schema:
    {{
      "target_leads": [
        {{"niche": "string", "search_query": "string"}},
        {{"niche": "string", "search_query": "string"}},
        {{"niche": "string", "search_query": "string"}}
      ]
    }}
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": BrainstormResult,
        },
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"target_leads": []}

if __name__ == "__main__":
    result = get_target_niches("Premium Website & AI Chatbot Development")
    print(json.dumps(result, indent=2))
