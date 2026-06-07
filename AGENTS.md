# Agent Architecture & Constraints Blueprint

## Target Infrastructure Environment:
- Hardware limits: Host device has 8GB RAM, 0 GPU.
- CRITICAL CONSTRAINT: Absolutely NO headless browsers (Playwright, Selenium, Puppeteer, Chromium, or Playwright-dependencies) are allowed in this codebase.
- Data fetching must rely purely on lightweight HTTP extraction strings via `requests` and `BeautifulSoup`.
- Multi-page auditing must be offloaded entirely to Google's cloud infrastructure via the Gemini API native `url_context` tool parameter.

## System Quota Safety Limits (Google AI Studio Free Tier):
- Maximum 10 Requests Per Minute (RPM)
- Maximum 1,500 Requests Per Day (RPD)
- Mandatory Multi-URL Bundle Strategy: 1 Lead Business = 1 Merged API Request (Homepage URL + extracted Service Drop-down URLs).
- Mandatory Global Throttle: Explicit 6-second sleep buffer following every lead completion.

## Codebase Modular Layout:
1. `brainstormer.py`: The Commander. Prompts Gemini to yield targeted local niche parameters and specific Google Maps query phrases.
2. `maps_scraper.py`: Extracts company baseline data and root domain targets via lightweight parsing.
3. `dropdown_finder.py`: Scans navigation structures to locate up to 4 high-ticket service sub-page links.
4. `cache_manager.py`: Connects to a local SQLite database (`cache.db`) to intercept duplication requests.
5. `gemini_auditor.py`: Performs multimodal cloud site assessment and scores leads using the Conversion Velocity Score (CVS) system.
6. `excel_exporter.py`: Formats code parameters, processes pandas logic, and sorts leads from lowest score to highest score.
7. `main.py`: The central pipeline orchestrator connecting all tasks.
