import requests
import re
import time
from typing import Dict, List, Optional
from enhanced_database import FindingsDB
from alerts import AlertManager
import json

class EnhancedCrawler:
    def __init__(self, config_path="config.json"):
        self.load_config(config_path)
        self.db = FindingsDB()
        self.session = self._setup_session()
        self.alert_manager = AlertManager(config_path)

    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            print(f"[+] Configuration loaded from {config_path}")
        except FileNotFoundError:
            print(f"[!] Config file not found: {config_path}")
            self.config = {}

    def _setup_session(self):
        """Setup requests session with Tor proxy"""
        session = requests.Session()
        tor_proxy = self.config.get("tor", {}).get("proxy", "socks5h://127.0.0.1:9150")
        session.proxies = {"http": tor_proxy, "https": tor_proxy}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        session.headers.update(headers)
        return session

    def fetch_page(self, url: str) -> Optional[str]:
        timeout = self.config.get("tor", {}).get("timeout", 60)
        retries = self.config.get("tor", {}).get("retries", 3)
        retry_delay = self.config.get("tor", {}).get("retry_delay", 5)

        for attempt in range(retries):
            try:
                print(f"[+] Fetching: {url} (attempt {attempt + 1}/{retries})")
                start = time.time()
                r = self.session.get(url, timeout=timeout, allow_redirects=True)
                duration = time.time() - start

                r.raise_for_status()
                self.db.log_crawl(url, "success", r.status_code, duration=duration)
                print(f"[+] Status: {r.status_code} ({duration:.2f}s)")
                return r.text

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                print(f"[!] HTTP error ({status}): {e}")
                if status == 429:
                    retry_after = e.response.headers.get("Retry-After") if e.response is not None else None
                    if retry_after and retry_after.isdigit():
                        wait = int(retry_after)
                    else:
                        wait = min(60, 5 * (attempt + 1))
                    print(f"[!] Rate limited (429). Waiting {wait}s before retry.")
                    time.sleep(wait)
                    continue
                if status in {502, 503, 504}:
                    print("[!] Server error; retrying")
                    time.sleep(retry_delay)
                    continue
                self.db.log_crawl(url, "error", status, str(e), duration)
                return None

            except requests.exceptions.Timeout:
                print(f"[!] Timeout on attempt {attempt + 1}")
                if attempt < retries - 1:
                    time.sleep(retry_delay)
                continue

            except requests.exceptions.ConnectionError as e:
                print(f"[!] Connection error: {e}")
                self.db.log_crawl(url, "failed", None, str(e), 0)
                if attempt < retries - 1:
                    time.sleep(retry_delay)
                continue

            except Exception as e:
                print(f"[!] Unexpected error: {e}")
                self.db.log_crawl(url, "error", None, str(e), 0)
                return None

        self.db.log_crawl(url, "failed", None, "Max retries exceeded", 0)
        return None

    def clean_html(self, html: str) -> str:
        # self.db.log_crawl(url, "failed", error="Max retries exceeded", duration=0)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        for tag in soup(["script", "style", "noscript", "meta"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_patterns(self, text: str, source_url: str) -> Dict[str, List[str]]:
        """Extract emails, phone numbers, API keys, etc using regex"""
        patterns = self.config.get("regex_patterns", {})
        extracted = {}

        for pattern_name, pattern in patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    extracted[pattern_name] = list(set(matches))[:50]  # Limit to 50 unique per type
                    print(f"[+] Found {len(matches)} {pattern_name}(s)")
                    for match in list(set(matches))[:5]:
                        self.db.add_extracted_data(source_url, match, pattern_name)
            except re.error as e:
                print(f"[!] Regex error for {pattern_name}: {e}")

        return extracted

    def search_keywords(self, text: str, source_url: str) -> Dict[str, float]:
        """Search for keywords AND company name with confidence scoring."""
        target_company = self.config.get("target_company", "")
        # Always include the company name as a search term
        keywords = list(self.config.get("keywords", []))
        if target_company and target_company.lower() not in [k.lower() for k in keywords]:
            keywords.append(target_company)

        text_lower = text.lower()
        matches = {}

        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                confidence = min(1.0, count / 10)
                matches[keyword] = confidence

                idx = text_lower.find(keyword.lower())
                snippet = text[max(0, idx - 100): idx + 200].strip()
                self.db.add_finding(keyword, snippet, source_url,
                                    confidence=confidence, target_company=target_company)
                print(f"[+] Found '{keyword}' ({count}x, confidence {confidence:.2f})")

        return matches

    def score_risk(self, keyword_matches: Dict[str, float], extracted: Dict[str, List[str]]) -> tuple[int, str, str]:
        """Assign a , risk level, and defensive recommendation."""
        score = 0
        risk_weights = self.config.get("risk_weights", {})
        data_weights = self.config.get("data_type_weights", {})
        recommendations = set()

        target_company = self.config.get("target_company", "").lower()
        for keyword, confidence in keyword_matches.items():
            # Company name on a dark web page is inherently high risk
            if target_company and keyword.lower() == target_company:
                weight = 20
            else:
                weight = risk_weights.get(keyword.lower(), 5)
            score += int(weight * confidence)
            if keyword.lower() in {"password", "api key", "token", "secret"}:
                recommendations.add("Rotate exposed credentials immediately and enable multi-factor authentication.")
            if keyword.lower() in {"credit card", "ssn", "email"}:
                recommendations.add("Monitor affected accounts and notify your security team for possible compromise.")
            if keyword.lower() in {"hack", "exploit", "vulnerability", "breach", "leak"}:
                recommendations.add("Investigate the source, patch vulnerable systems, and consider breach response procedures.")
            if keyword.lower() == "database":
                recommendations.add("Audit database access and review exposed data classifications.")
            if keyword.lower() == "apple":
                recommendations.add("Prioritize review of any brand-related or company-specific data leakage.")

        for data_type, values in extracted.items():
            weight = data_weights.get(data_type.lower(), 10)
            score += weight * len(values)
            if data_type.lower() in {"credit_card", "ssn", "api_key"}:
                recommendations.add("Treat this as a high-priority incident and revoke compromised values immediately.")
            if data_type.lower() == "email":
                recommendations.add("Validate exposed email addresses and watch for phishing campaigns.")

        score = min(100, score)

        if score >= 80:
            risk_level = "Critical"
        elif score >= 50:
            risk_level = "High"
        elif score >= 25:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        if not recommendations:
            recommendations.add("Continue monitoring this source and maintain normal security vigilance.")

        return score, risk_level, " ".join(sorted(recommendations))

    # Domains that are search/index engines — never generate findings from them
    DISCOVERY_ONLY_DOMAINS = {
        "juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",  # Ahmia
        "torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion",  # Torch
        "tordexu73joywapk2txdr54jed4imqledpcvcuf75qsas2gwdgksvnyd.onion",   # TorDex
        "msydqstlz2kzerdg.onion",   # old Ahmia
        "expyuzz4wqqyqhjn.onion",   # Tor Project (dead)
    }

    def crawl_url(self, url: str) -> bool:
        """Crawl a single URL and analyze content"""
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""

        if hostname in self.DISCOVERY_ONLY_DOMAINS:
            print(f"[~] Skipping search-engine domain (discovery only): {url}")
            return False

        print(f"\n{'='*60}")
        print(f"[*] Crawling: {url}")
        print(f"{'='*60}")

        html = self.fetch_page(url)
        if not html:
            return False

        # Extract clean text
        text = self.clean_html(html)
        print(f"[+] Page size: {len(text)} characters")

        # Only analyse pages that mention the target company
        target_company = self.config.get("target_company", "")
        if target_company and target_company.lower() not in text.lower():
            print(f"[-] '{target_company}' not found on page — skipping")
            return False

        print(f"[+] '{target_company}' mentioned on page — analysing...")

        # Search keywords
        keyword_matches = self.search_keywords(text, url)

        # Extract patterns
        extracted = self.extract_patterns(text, url)

        # Risk scoring
        risk_score, risk_level, recommendations = self.score_risk(keyword_matches, extracted)
        self.db.add_risk_assessment(url, risk_score, risk_level, recommendations)
        self.db.update_findings_risk(url, risk_score, risk_level)
        print(f"[+] Risk score: {risk_score} ({risk_level})")
        print(f"[+] Recommendation: {recommendations}")

        # Send Telegram alert for High / Critical findings
        if risk_score >= 70 and (keyword_matches or extracted):
            top_keyword = max(keyword_matches, key=keyword_matches.get) if keyword_matches else "N/A"
            snippet = ""
            if top_keyword != "N/A":
                idx = text.lower().find(top_keyword.lower())
                snippet = text[max(0, idx - 80): idx + 200].strip()

            finding = {
                "url":            url,
                "keyword":        top_keyword,
                "snippet":        snippet,
                "risk_score":     risk_score,
                "confidence":     round(keyword_matches.get(top_keyword, 0) * 100),
                "classification": risk_level,
            }
            result = self.alert_manager.send_alert(finding, risk_level.lower())
            if result.get("sent"):
                print(f"[+] Telegram alert sent (risk={risk_score})")
            elif result.get("suppressed"):
                print(f"[~] Telegram alert suppressed (duplicate)")
            else:
                print(f"[!] Telegram alert failed: {result.get('message')}")

        if keyword_matches or extracted:
            print(f"[+] Analysis complete. Found {len(keyword_matches)} keywords and {len(extracted)} data patterns")
            return True
        else:
            print(f"[-] No keywords or patterns found")
            return False

    def crawl_batch(self, urls: List[str]):
        """Crawl multiple URLs"""
        delay = self.config.get("crawling", {}).get("delay_between_requests", 2)
        
        for i, url in enumerate(urls):
            self.crawl_url(url)
            if i < len(urls) - 1:
                print(f"[*] Waiting {delay}s before next request...")
                time.sleep(delay)

    def print_stats(self):
        """Print crawling statistics"""
        stats = self.db.get_stats()
        print(f"\n{'='*60}")
        print(f"[*] CRAWLING STATISTICS")
        print(f"{'='*60}")
        print(f"Total findings: {stats['total_findings']}")
        print(f"Successful crawls: {stats['successful_crawls']}")
        print(f"Extracted data points: {stats['extracted_data_points']}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    crawler = EnhancedCrawler()
    
    # Get seed URLs from config
    seed_urls = crawler.config.get("seed_urls", [])
    if seed_urls:
        crawler.crawl_batch(seed_urls)
    
    crawler.print_stats()
