                      
"""
Database query tool for analyzing findings
"""

import sqlite3
from tabulate import tabulate
from collections import defaultdict

class FindingsAnalyzer:
    def __init__(self, db_name="findings.db"):
        self.db_name = db_name

    def query(self, sql, params=()):
        """Execute a query and return results"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(sql, params)
        results = c.fetchall()
        conn.close()
        return results

    def show_recent_findings(self, limit=20):
        """Show most recent findings"""
        results = self.query(
            "SELECT keyword, snippet, source_url, confidence_score, found_at FROM findings ORDER BY found_at DESC LIMIT ?",
            (limit,)
        )
        
        if results:
            print(f"\n{'='*100}")
            print(f"RECENT FINDINGS (Last {limit})")
            print(f"{'='*100}\n")
            headers = ["Keyword", "Snippet", "Source URL", "Confidence", "Found At"]
            for row in results:
                print(f"Keyword: {row[0]}")
                print(f"Snippet: {row[1][:100]}...")
                print(f"Source: {row[2]}")
                print(f"Confidence: {row[3]:.2f}")
                print(f"Time: {row[4]}\n")
        else:
            print("[-] No findings in database")

    def show_apple_findings(self, limit=50):
        """Show findings related to Apple"""
        results = self.query(
            "SELECT keyword, snippet, source_url, confidence_score, found_at FROM findings WHERE keyword='apple' OR snippet LIKE '%apple%' ORDER BY found_at DESC LIMIT ?",
            (limit,)
        )
        
        if results:
            print(f"\n{'='*100}")
            print(f"APPLE-RELATED FINDINGS (Last {limit})")
            print(f"{'='*100}\n")
            for row in results:
                print(f"Keyword: {row[0]}")
                print(f"Snippet: {row[1][:200]}...")
                print(f"Source: {row[2]}")
                print(f"Confidence: {row[3]:.2f}")
                print(f"Time: {row[4]}\n")
        else:
            print("[-] No Apple-related findings in database")

    def show_extracted_data(self):
        """Show extracted emails, phone numbers, etc"""
        results = self.query(
            "SELECT data_type, COUNT(*) as count FROM extracted_data GROUP BY data_type ORDER BY count DESC"
        )
        
        if results:
            print(f"\n{'='*60}")
            print(f"EXTRACTED DATA SUMMARY")
            print(f"{'='*60}\n")
            for data_type, count in results:
                print(f"{data_type.upper()}: {count} extracted")
            print()
        
                                        
        data_types = self.query("SELECT DISTINCT data_type FROM extracted_data ORDER BY data_type")
        
        for (data_type,) in data_types:
            samples = self.query(
                "SELECT data_value, COUNT(*) FROM extracted_data WHERE data_type=? GROUP BY data_value LIMIT 5",
                (data_type,)
            )
            if samples:
                print(f"\nSample {data_type.upper()} values:")
                for value, count in samples:
                    print(f"  - {value} (found {count} time(s))")

    def show_crawl_stats(self):
        """Show crawling statistics"""
        results = self.query(
            "SELECT status, COUNT(*) as count FROM crawl_history GROUP BY status"
        )
        
        print(f"\n{'='*60}")
        print(f"CRAWL STATISTICS")
        print(f"{'='*60}\n")
        
        for status, count in results:
            print(f"{status.upper()}: {count}")
        
                          
        duration = self.query("SELECT AVG(duration_seconds) FROM crawl_history WHERE status='success'")
        if duration[0][0]:
            print(f"Avg Duration: {duration[0][0]:.2f}s")
        print()

    def show_keyword_summary(self):
        """Show keyword frequency"""
        results = self.query(
            "SELECT keyword, COUNT(*) as count, AVG(confidence_score) as avg_confidence FROM findings GROUP BY keyword ORDER BY count DESC"
        )
        
        print(f"\n{'='*60}")
        print(f"KEYWORD SUMMARY")
        print(f"{'='*60}\n")
        
        for keyword, count, avg_conf in results:
            print(f"{keyword.upper()}: {count} matches (avg confidence: {avg_conf:.2f})")
        print()

    def show_risk_summary(self):
        """Show risk levels summary"""
        results = self.query(
            "SELECT risk_level, COUNT(*) as count FROM risk_assessment GROUP BY risk_level ORDER BY count DESC"
        )
        print(f"\n{'='*60}")
        print(f"RISK LEVEL SUMMARY")
        print(f"{'='*60}\n")
        if results:
            for risk_level, count in results:
                print(f"{risk_level}: {count}")
        else:
            print("[-] No risk assessments available")
        print()

    def show_url_risk_details(self, limit=20):
        """Show top risk URLs"""
        results = self.query(
            "SELECT source_url, risk_score, risk_level, recommendations FROM risk_assessment ORDER BY risk_score DESC LIMIT ?",
            (limit,)
        )
        print(f"\n{'='*100}")
        print(f"TOP URL RISK DETAILS (Last {limit})")
        print(f"{'='*100}\n")
        if results:
            for source_url, score, level, recs in results:
                print(f"URL: {source_url}")
                print(f"Score: {score} ({level})")
                print(f"Recommendations: {recs}\n")
        else:
            print("[-] No risk details available")
        print()

    def show_urls_by_findings(self):
        """Show which URLs had the most findings"""
        results = self.query(
            "SELECT source_url, COUNT(*) as count FROM findings GROUP BY source_url ORDER BY count DESC LIMIT 10"
        )
        
        print(f"\n{'='*60}")
        print(f"TOP URLS BY FINDINGS")
        print(f"{'='*60}\n")
        
        for url, count in results:
            print(f"{url}: {count} findings")
        print()

    def full_report(self):
        """Generate full analysis report"""
        print(f"\n{'#'*60}")
        print(f"# DARK WEB OSINT - FULL ANALYSIS REPORT")
        print(f"{'#'*60}")
        
        self.show_keyword_summary()
        self.show_risk_summary()
        self.show_url_risk_details(10)
        self.show_urls_by_findings()
        self.show_extracted_data()
        self.show_crawl_stats()
        self.show_recent_findings()
        
        print(f"\n{'#'*60}")
        print(f"# END OF REPORT")
        print(f"{'#'*60}\n")

if __name__ == "__main__":
    import sys
    from enhanced_database import FindingsDB
    
    FindingsDB()                                                       
    analyzer = FindingsAnalyzer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--recent":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            analyzer.show_recent_findings(limit)
        elif command == "--extracted":
            analyzer.show_extracted_data()
        elif command == "--keywords":
            analyzer.show_keyword_summary()
        elif command == "--urls":
            analyzer.show_urls_by_findings()
        elif command == "--risk":
            analyzer.show_risk_summary()
        elif command == "--risk-details":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            analyzer.show_url_risk_details(limit)
        elif command == "--apple-risk":
            analyzer.show_apple_risk()
        elif command == "--stats":
            analyzer.show_crawl_stats()
        elif command == "--apple":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            analyzer.show_apple_findings(limit)
        elif command == "--full":
            analyzer.full_report()
        else:
            print("Unknown command")
    else:
        analyzer.full_report()
