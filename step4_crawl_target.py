import requests
import sqlite3
from bs4 import BeautifulSoup

                                              
TOR_PROXY = "socks5h://127.0.0.1:9150"

session = requests.Session()
session.proxies = {"http": TOR_PROXY, "https": TOR_PROXY}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

KEYWORDS = ["leak", "password", "email"]

                                              
def fetch(url, timeout=60):
    try:
        r = session.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[!] Fetch failed: {e}")
        return None

                                              
def extract_clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return text

                                                
def save_matches(text, source_url):
    conn = sqlite3.connect("findings.db")
    c = conn.cursor()

    text_lower = text.lower()

    for kw in KEYWORDS:
        if kw in text_lower:
            snippet = text_lower[:300]
            c.execute(
                "INSERT INTO findings (keyword, snippet, source_url) VALUES (?, ?, ?)",
                (kw, snippet, source_url)
            )
            print(f"[+] Saved match for keyword: {kw}")

    conn.commit()
    conn.close()

                                        
if __name__ == "__main__":
    TARGET_ONION = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"

    html = fetch(TARGET_ONION)
    if not html:
        raise SystemExit(1)

    text = extract_clean_text(html)
    save_matches(text, TARGET_ONION)

    print("Done.")
