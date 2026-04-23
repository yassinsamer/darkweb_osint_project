import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

TOR_PROXY = "socks5h://127.0.0.1:9150"

session = requests.Session()
session.proxies = {"http": TOR_PROXY, "https": TOR_PROXY}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

AHMIA_HOME = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"

def fetch(url, timeout=60):
    try:
        r = session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[!] Fetch failed: {e}")
        return None

def extract_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"].strip())
        links.add(full)

    return sorted(links)

def only_onion_links(links):
    onion = []
    for link in links:
        host = urlparse(link).hostname or ""
        if host.endswith(".onion"):
            onion.append(link)
    return onion

if __name__ == "__main__":
    print("=== STEP 3: PARSE AHMIA HOMEPAGE ===\n")

    html = fetch(AHMIA_HOME)
    if not html:
        raise SystemExit(1)

    all_links = extract_links(AHMIA_HOME, html)
    onion_links = only_onion_links(all_links)

    print(f"[+] Total links found: {len(all_links)}")
    print(f"[+] .onion links found: {len(onion_links)}")

    with open("ahmia_links.txt", "w", encoding="utf-8") as f:
        for link in all_links:
            f.write(link + "\n")

    with open("ahmia_onion_links.txt", "w", encoding="utf-8") as f:
        for link in onion_links:
            f.write(link + "\n")

    print("[+] Saved ahmia_links.txt and ahmia_onion_links.txt")
