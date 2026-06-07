import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

def get_business_domains(search_query: str, city: str = "New York", mock_fallback: bool = True) -> list:
    """
    Attempts to scrape Google Search for local businesses.
    If blocked or unsuccessful, returns a mock list of highly realistic valid local business URLs.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    query = f"{search_query} {city}".replace(" ", "+")
    url = f"https://www.google.com/search?q={query}"

    domains = set()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Google search organic links often wrapped in <a href="url"> inside specific div classes
            # Since classes change often, we do a basic regex on all hrefs that look like valid external domains
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and not 'google.com' in href:
                    parsed = urlparse(href)
                    domain = f"{parsed.scheme}://{parsed.netloc}"
                    domains.add(domain)
                    if len(domains) >= 10:
                        break
    except requests.RequestException:
        pass

    if not domains and mock_fallback:
        # Graceful fallback to mock data as requested
        return [
            "https://www.nycroofers.com",
            "https://www.manhattandentalcare.com",
            "https://www.sohoaesthetics.com",
            "https://www.brooklynplumbingpros.com",
            "https://www.queenslandscaping.com",
            "https://www.statenislandhvac.com",
            "https://www.nyccustombuilders.com",
            "https://www.midtownchiropractic.com",
            "https://www.chelseavetclinic.com",
            "https://www.tribecacontractors.com"
        ]

    return list(domains)[:10]

if __name__ == "__main__":
    print(get_business_domains("roofing contractors"))
