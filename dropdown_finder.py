import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def get_dropdown_links(base_url: str) -> dict:
    """
    Fetches the homepage HTML and extracts up to 4 service/sub-page URLs
    often found in dropdown menus or main navigation.
    Also extracts any visible business contact emails via regex.
    Returns a dict with 'links' (list) and 'emails' (list).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        # Gracefully handle unreachable websites
        return {"links": [], "emails": []}

    html_text = response.text
    soup = BeautifulSoup(html_text, "html.parser")

    sub_urls = set()

    # Extract emails using regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    found_emails = list(set(re.findall(email_pattern, html_text)))

    # Target <nav>, <ul>, or elements with classes like 'menu', 'nav', 'dropdown'
    nav_elements = soup.find_all(['nav', 'ul'])
    for el in nav_elements:
        links = el.find_all('a', href=True)
        for link in links:
            href = link.get('href').lower()
            if any(keyword in href for keyword in ['/service', '/our-work', '/treatments', '/procedures']):
                full_url = urljoin(base_url, link.get('href'))
                sub_urls.add(full_url)
                if len(sub_urls) >= 4:
                    return {"links": list(sub_urls), "emails": found_emails}

    # Fallback: if specific keywords aren't found, just grab any links in <nav> up to 4
    if not sub_urls:
        for el in nav_elements:
            links = el.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href and href.startswith('/') and len(href) > 1:
                    full_url = urljoin(base_url, href)
                    sub_urls.add(full_url)
                    if len(sub_urls) >= 4:
                        return {"links": list(sub_urls), "emails": found_emails}

    return {"links": list(sub_urls)[:4], "emails": found_emails}

if __name__ == "__main__":
    # Test with a dummy or real URL just to show it handles logic (use a non-blocking one)
    print(get_dropdown_links("https://example.com"))
