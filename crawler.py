import requests
import time

TOR_PROXY = "socks5h://127.0.0.1:9150"

session = requests.Session()
session.proxies = {"http": TOR_PROXY, "https": TOR_PROXY}

# Browser-like headers (important to avoid 403)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def fetch_onion_page(url, timeout=60):
    try:
        print(f"[+] Fetching: {url}")
        r = session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        print(f"[+] Status: {r.status_code}")
        r.raise_for_status()
        return r.text
    except requests.exceptions.HTTPError as e:
        print(f"[!] HTTP error: {e}")
        # Print a small preview (sometimes includes reason)
        if hasattr(e, "response") and e.response is not None:
            print("[!] Response preview:", e.response.text[:200])
    except Exception as e:
        print(f"[!] Fetch failed: {e}")
    return None

if __name__ == "__main__":
    onion_url = "http://7ukmkdtyxdkdivtjad57klqnd3kdsmq6tp45rrsxqnu76zzv3jvitlqd.onion/Converted_to_PDF/"
    html = fetch_onion_page(onion_url)
    if html:
        print("\n=== FIRST 500 CHARS ===\n")
        print(html[:500])
