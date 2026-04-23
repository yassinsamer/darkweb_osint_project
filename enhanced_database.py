import sqlite3
from datetime import datetime
from pathlib import Path

class FindingsDB:
    def __init__(self, db_name="findings.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialize or upgrade database schema"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

                                                               
        c.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                keyword TEXT,
                snippet TEXT,
                confidence REAL,
                risk_score REAL,
                classification TEXT,
                target_company TEXT DEFAULT '',
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

                                                            
        try:
            c.execute("ALTER TABLE findings ADD COLUMN target_company TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass                         

                                             
        c.execute("""
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT,
                status_code INTEGER,
                error_message TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_seconds REAL
            )
        """)

                                               
        c.execute("""
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id INTEGER,
                data_type TEXT,
                data_value TEXT,
                FOREIGN KEY(finding_id) REFERENCES findings(id)
            )
        """)

                                            
        c.execute("""
            CREATE TABLE IF NOT EXISTS url_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        """)

                                         
        c.execute("""
            CREATE TABLE IF NOT EXISTS risk_assessment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT UNIQUE NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                recommendations TEXT,
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

                                        
        c.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON findings(keyword)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_found_at ON findings(found_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_url_status ON crawl_history(url, status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON url_queue(status)")

        conn.commit()
        conn.close()
        print(f"[+] Database '{self.db_name}' initialized")

    def add_finding(self, keyword, snippet, source_url, data_type=None, confidence=0.5, target_company=''):
        """Add a keyword finding"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "INSERT INTO findings (url, keyword, snippet, confidence, target_company) VALUES (?, ?, ?, ?, ?)",
            (source_url, keyword, snippet[:500], confidence, target_company)
        )
        conn.commit()
        conn.close()

    def update_findings_risk(self, source_url, risk_score, risk_level):
        """Backfill risk_score and classification for all findings from a URL"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "UPDATE findings SET risk_score=?, classification=? WHERE url=? AND risk_score IS NULL",
            (risk_score, risk_level, source_url)
        )
        conn.commit()
        conn.close()

    def add_extracted_data(self, source_url, data_value, data_type):
        """Add extracted patterns (emails, phone numbers, etc)"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO extracted_data (data_type, data_value) VALUES (?, ?)",
                (data_type, data_value)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass                   
        finally:
            conn.close()

    def add_risk_assessment(self, source_url, risk_score, risk_level, recommendations):
        """Store or update risk assessment for a URL"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "INSERT INTO risk_assessment (source_url, risk_score, risk_level, recommendations) VALUES (?, ?, ?, ?)"
            "ON CONFLICT(source_url) DO UPDATE SET risk_score=excluded.risk_score, risk_level=excluded.risk_level, recommendations=excluded.recommendations, assessed_at=CURRENT_TIMESTAMP",
            (source_url, risk_score, risk_level, recommendations)
        )
        conn.commit()
        conn.close()

    def get_risk_summary(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT risk_level, COUNT(*) FROM risk_assessment GROUP BY risk_level")
        results = c.fetchall()
        conn.close()
        return results

    def get_apple_risk_summary(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "SELECT source_url, risk_score, risk_level, recommendations FROM risk_assessment WHERE source_url IN (SELECT DISTINCT source_url FROM findings WHERE keyword='apple' OR snippet LIKE '%apple%') ORDER BY risk_score DESC"
        )
        results = c.fetchall()
        conn.close()
        return results

    def log_crawl(self, url, status, status_code=None, error=None, duration=0):
        """Log crawl attempt"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "INSERT INTO crawl_history (url, status, status_code, error_message, duration_seconds) VALUES (?, ?, ?, ?, ?)",
            (url, status, status_code, error, duration)
        )
        conn.commit()
        conn.close()

    def add_url_to_queue(self, url, priority=0):
        """Add URL to crawl queue, or re-queue it if already processed"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO url_queue (url, priority) VALUES (?, ?)",
                (url, priority)
            )
        except sqlite3.IntegrityError:
                                                                            
            c.execute(
                "UPDATE url_queue SET status='pending', priority=?, processed_at=NULL WHERE url=?",
                (priority, url)
            )
        conn.commit()
        conn.close()

    def reset_queue(self):
        """Mark all processed URLs as pending so they get re-crawled next cycle"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("UPDATE url_queue SET status='pending', processed_at=NULL WHERE status='processed'")
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected

    def get_pending_urls(self, limit=10):
        """Get next batch of URLs to crawl"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "SELECT id, url FROM url_queue WHERE status='pending' ORDER BY priority DESC LIMIT ?",
            (limit,)
        )
        results = c.fetchall()
        conn.close()
        return results

    def mark_url_processed(self, url_id):
        """Mark URL as processed"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "UPDATE url_queue SET status='processed', processed_at=CURRENT_TIMESTAMP WHERE id=?",
            (url_id,)
        )
        conn.commit()
        conn.close()

    def get_stats(self):
        """Get crawling statistics"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM findings")
        findings_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM crawl_history WHERE status='success'")
        successful_crawls = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM extracted_data")
        extracted_count = c.fetchone()[0]
        
        conn.close()
        return {
            "total_findings": findings_count,
            "successful_crawls": successful_crawls,
            "extracted_data_points": extracted_count
        }

if __name__ == "__main__":
    db = FindingsDB()
    stats = db.get_stats()
    print(f"[+] Stats: {stats}")
