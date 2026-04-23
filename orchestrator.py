                      
"""
Master orchestrator for automated dark web OSINT crawling
Coordinates: Ahmia parsing -> URL discovery -> Distributed crawling
"""

import re
import schedule
import time
import threading
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enhanced_crawler import EnhancedCrawler
from enhanced_database import FindingsDB
from urllib.parse import urlparse

                                                      
_ONION_RE = re.compile(r'https?://[a-z2-7]{16,56}\.onion[^\s"\'<>]*', re.IGNORECASE)

class DarkWebOrchestrator:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()
        self.db = FindingsDB()
        self.crawler = EnhancedCrawler(config_path)
        self.running = True

    def load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"[!] Config file not found: {self.config_path}")
            self.config = {}

                                                                             
    _SEARCH_ENGINE_HOSTS = {
        "juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",         
        "torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion",         
        "tordexu73joywapk2txdr54jed4imqledpcvcuf75qsas2gwdgksvnyd.onion",           
    }

    def _extract_onion_urls(self, html, exclude_hosts=None):
        """Extract every .onion URL from raw HTML using regex — works regardless of HTML structure."""
        exclude_hosts = exclude_hosts or set()
        found = set()
        for url in _ONION_RE.findall(html):
            host = urlparse(url).hostname or ""
            if host not in exclude_hosts:
                found.add(url.rstrip(".,)\"'"))
        return found

    def discover_urls_from_ahmia(self):
        """Search Ahmia for the target company and queue every result URL found."""
        print(f"\n{'='*60}")
        print(f"[*] STEP 1: Searching Ahmia for target company")
        print(f"{'='*60}")

        ahmia_base = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"
        target_company = self.config.get("target_company", "")

        if not target_company:
            print("[!] No target company set — skipping Ahmia search")
            return []

        search_terms = [
            target_company,
            f"{target_company} leak",
            f"{target_company} breach",
            f"{target_company} password",
            f"{target_company} database",
        ]

        discovered_urls = set()

        for term in search_terms:
            search_url = f"{ahmia_base}/search/?q={term.replace(' ', '+')}"
            print(f"[+] Ahmia: {search_url}")

            html = self.fetch_with_backoff(search_url)
            if not html:
                print(f"[!] No response from Ahmia for '{term}'")
                continue

            urls = self._extract_onion_urls(html, exclude_hosts=self._SEARCH_ENGINE_HOSTS)
            for url in urls:
                discovered_urls.add(url)
                self.db.add_url_to_queue(url, priority=3)
            print(f"[+] Ahmia '{term}': found {len(urls)} URLs")

        print(f"[+] Ahmia total: {len(discovered_urls)} unique external URLs queued")
        return list(discovered_urls)

    def discover_urls_from_torch(self, company_name):
        """Search Torch for the target company and queue every result URL found."""
        print(f"\n{'='*60}")
        print(f"[*] STEP 1B: Searching Torch for '{company_name}'")
        print(f"{'='*60}")

        torch_base = "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion"
        search_terms = [
            company_name,
            f"{company_name} leak",
            f"{company_name} breach",
            f"{company_name} password",
            f"{company_name} hack",
            f"{company_name} database",
        ]

        discovered_urls = set()

        for term in search_terms:
            search_url = f"{torch_base}/?q={term.replace(' ', '+')}"
            print(f"[+] Torch: {search_url}")

            html = self.fetch_with_backoff(search_url)
            if not html:
                print(f"[!] Failed to fetch Torch for '{term}'")
                continue

            urls = self._extract_onion_urls(html, exclude_hosts=self._SEARCH_ENGINE_HOSTS)
            for url in urls:
                discovered_urls.add(url)
                self.db.add_url_to_queue(url, priority=5)
            print(f"[+] Torch '{term}': found {len(urls)} URLs")

        print(f"[+] Torch total: {len(discovered_urls)} unique external URLs queued")
        return list(discovered_urls)

    def fetch_with_backoff(self, url, max_attempts=4):
        """Fetch page with exponential backoff for rate-limited responses"""
        for attempt in range(1, max_attempts + 1):
            html = self.crawler.fetch_page(url)
            if html:
                return html
            delay = min(30, 5 * attempt)
            print(f"[!] Backoff: waiting {delay}s before retry {attempt}/{max_attempts}")
            time.sleep(delay)
        return None

    def crawl_queue_distributed(self, max_workers=None):
        """Crawl URLs from queue using thread pool"""
        if max_workers is None:
            max_workers = self.config.get("crawling", {}).get("max_workers", 5)

        print(f"\n{'='*60}")
        print(f"[*] STEP 2: Distributed Crawling ({max_workers} workers)")
        print(f"{'='*60}")

        batch_size = self.config.get("crawling", {}).get("batch_size", 10)
        pending_urls = self.db.get_pending_urls(limit=batch_size)

        if not pending_urls:
            print("[!] No URLs in queue to crawl")
            return

        print(f"[+] Processing {len(pending_urls)} URLs...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for url_id, url in pending_urls:
                future = executor.submit(self._crawl_and_mark, url_id, url)
                futures[future] = (url_id, url)

            completed = 0
            for future in as_completed(futures):
                url_id, url = futures[future]
                try:
                    future.result()
                    completed += 1
                    print(f"[+] Progress: {completed}/{len(pending_urls)}")
                except Exception as e:
                    print(f"[!] Error crawling {url}: {e}")

    def _crawl_and_mark(self, url_id, url):
        """Helper to crawl URL and mark as processed"""
        try:
            self.crawler.crawl_url(url)
        finally:
            self.db.mark_url_processed(url_id)

    def add_seed_urls(self):
        """Add seed URLs from config to queue"""
        seed_urls = self.config.get("seed_urls", [])
        print(f"\n[*] Adding {len(seed_urls)} seed URLs to queue...")
        for url in seed_urls:
            self.db.add_url_to_queue(url, priority=10)                 

    def run_full_cycle(self):
        """Execute full crawling cycle"""
        print(f"\n{'#'*60}")
        print(f"# DARK WEB OSINT ORCHESTRATOR - CYCLE START")
        print(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")

        try:
                                                                    
            reset_count = self.db.reset_queue()
            print(f"[*] Reset {reset_count} previously-processed URLs to pending")

                           
            self.add_seed_urls()

                                                                          
            self.discover_urls_from_ahmia()

                                                  
            target_company = self.config.get("target_company")
            if target_company and target_company != "example_company":
                self.discover_urls_from_torch(target_company)

                                                                              
            self.crawl_queue_distributed()
            
                              
            self.crawler.print_stats()

        except Exception as e:
            print(f"[!] Error in full cycle: {e}")

        print(f"\n{'#'*60}")
        print(f"# CYCLE COMPLETE")
        print(f"{'#'*60}\n")

    def schedule_crawling(self):
        """Setup automated scheduling"""
        interval = self.config.get("scheduling", {}).get("interval_minutes", 60)
        
        schedule.every(interval).minutes.do(self.run_full_cycle)
        print(f"[+] Scheduled crawling every {interval} minutes")

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def run_once(self):
        """Run a single crawling cycle"""
        self.run_full_cycle()

    def run_scheduled(self):
        """Run with scheduling enabled"""
        try:
            self.schedule_crawling()
        except KeyboardInterrupt:
            print("\n[*] Shutting down orchestrator...")
            self.running = False

    def generate_report(self):
        """Generate findings report"""
        stats = self.db.get_stats()
        
        report = f"""
{'='*60}
DARK WEB OSINT FINDINGS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

STATISTICS:
- Total Findings: {stats['total_findings']}
- Successful Crawls: {stats['successful_crawls']}
- Extracted Data Points: {stats['extracted_data_points']}

DATABASE LOCATION: findings.db

Use the following commands to query findings:
  sqlite3 findings.db "SELECT * FROM findings ORDER BY found_at DESC;"
  sqlite3 findings.db "SELECT data_type, COUNT(*) FROM extracted_data GROUP BY data_type;"
  sqlite3 findings.db "SELECT * FROM crawl_history WHERE status='success';"

{'='*60}
        """
        
        print(report)
        with open("findings_report.txt", "w") as f:
            f.write(report)
        print("[+] Report saved to findings_report.txt")

if __name__ == "__main__":
    import sys

    orchestrator = DarkWebOrchestrator()

    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        print("[*] Running with scheduling enabled...")
        orchestrator.run_scheduled()
    else:
        print("[*] Running one cycle...")
        orchestrator.run_once()
        orchestrator.generate_report()
