# Dark Web OSINT Automation System - ENHANCED

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Tor Browser running (SOCKS5 on 127.0.0.1:9150)
- Dependencies installed

### Installation
```bash
pip install -r requirements.txt
```

## 📋 Components

### 1. **config.json** (Configuration Hub)
Central configuration for all crawling operations:
- Tor proxy settings
- Keyword list (15+ pre-configured)
- Regex patterns (emails, phone, SSN, API keys, credit cards)
- Crawling parameters (workers, delays, timeouts)
- Scheduling settings
- Seed URLs

Edit this file to customize behavior without touching code.

### 2. **enhanced_database.py** (Advanced Data Management)
Enhanced database with multiple tables:
- `findings` - Keyword matches with confidence scoring
- `crawl_history` - Track all crawl attempts and errors
- `extracted_data` - Structured data (emails, phones, etc.)
- `url_queue` - Distributed crawling queue with priorities

**Key Features:**
- Automatic schema management
- Indexed queries for speed
- Duplicate prevention
- Progress tracking

### 3. **enhanced_crawler.py** (Smart Crawler)
Core crawling engine with intelligent features:
- **Retry logic** - Auto-retries with exponential backoff
- **Pattern extraction** - Emails, phones, APIs, SSNs, credit cards
- **Keyword matching** - Confidence scoring based on frequency
- **Error recovery** - Graceful handling of Tor disconnects
- **Request throttling** - Respectful delays between requests

### 4. **orchestrator.py** (Master Automation)
Main orchestrator that coordinates everything:

**Run one cycle:**
```bash
python orchestrator.py
```

**Run continuously with scheduling:**
```bash
python orchestrator.py --scheduled
```

**What it does:**
1. Seeds URL queue with configured URLs
2. Discovers new .onion URLs from Ahmia homepage
3. Distributes crawling across worker threads
4. Logs all activity and findings
5. Auto-generates reports

### 5. **query_database.py** (Analysis & Reporting)
Query and analyze findings:

```bash
# Full report
python query_database.py --full

# Recent findings
python query_database.py --recent 50

# Extracted data summary
python query_database.py --extracted

# Keywords frequency
python query_database.py --keywords

# Crawl statistics
python query_database.py --stats

# Top URLs by findings
python query_database.py --urls
```

## 🔄 Workflow

```
CONFIG.JSON
    ↓
ORCHESTRATOR.PY
    ├─→ Add Seed URLs (from config)
    ├─→ Discover URLs (from Ahmia)
    ├─→ Populate Queue (enhanced_database.py)
    └─→ Distributed Crawling (enhanced_crawler.py × N workers)
        ├─→ Fetch page
        ├─→ Extract clean text
        ├─→ Search keywords
        ├─→ Extract patterns
        └─→ Save to DB
    ↓
FINDINGS.DB (SQLite)
    ├─ findings table
    ├─ extracted_data table
    ├─ crawl_history table
    └─ url_queue table
    ↓
QUERY_DATABASE.PY → Reports & Analysis
```

## ⚙️ Configuration Examples

### Increase crawling speed:
```json
"crawling": {
  "max_workers": 10,
  "delay_between_requests": 1
}
```

### Add custom keywords:
```json
"keywords": [
  "your_keyword_here",
  "sensitive_data"
]
```

### Add custom regex pattern:
```json
"regex_patterns": {
  "bitcoin_wallet": "\\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\\b"
}
```

### Enable hourly crawling (9 AM - 5 PM):
```json
"scheduling": {
  "enable_scheduler": true,
  "interval_minutes": 60,
  "start_hour": 9,
  "end_hour": 17
}
```

## 📊 Database Queries

### Find all leaked emails:
```bash
sqlite3 findings.db "SELECT DISTINCT data_value FROM extracted_data WHERE data_type='email';"
```

### Get high-confidence findings:
```bash
sqlite3 findings.db "SELECT * FROM findings WHERE confidence_score > 0.8 ORDER BY found_at DESC;"
```

### Crawl performance:
```bash
sqlite3 findings.db "SELECT status, AVG(duration_seconds) FROM crawl_history GROUP BY status;"
```

### URLs never successfully crawled:
```bash
sqlite3 findings.db "SELECT url FROM url_queue WHERE status='pending' LIMIT 10;"
```

## 🔐 Security Notes

- Always run behind Tor
- Use rotating IP proxies for large-scale crawling
- Implement request rate limiting (configured via delay_between_requests)
- Monitor Tor logs for connection issues
- Backup findings.db regularly
- Consider encrypting database for sensitive operations

## 🚦 Automation Features

✅ **Automatic URL Discovery** - Ahmia parsing finds new targets
✅ **Distributed Crawling** - Multiple workers = faster results
✅ **Intelligent Retries** - Auto-recovery from Tor failures
✅ **Pattern Extraction** - Emails, phones, APIs automatically extracted
✅ **Confidence Scoring** - Keywords ranked by match quality
✅ **Scheduling** - Continuous background operation
✅ **Progress Tracking** - Know exactly what's been crawled
✅ **Error Logging** - Learn why crawls fail
✅ **Auto Reports** - Generated after each cycle

## 🛠️ Troubleshooting

**"Tor proxy connection failed"**
- Ensure Tor Browser is running on 127.0.0.1:9150
- Check firewall settings

**"Timeout errors"**
- Increase timeout in config.json
- Reduce max_workers
- Check your internet connection

**"No findings after crawling"**
- Check if target URLs exist
- Verify keywords are appropriate
- Check crawler.py output for errors

**"Database locked error"**
- Close other database connections
- Remove findings.db and restart

## 📈 Scaling

For larger operations:
1. Increase `max_workers` (10-20 is reasonable)
2. Reduce `delay_between_requests` (1-2 seconds)
3. Run multiple instances with different seed URLs
4. Consider using residential proxies for anonymity
5. Monitor Tor relay statistics

## 📝 Example Usage

### Full automated cycle with reporting:
```bash
python orchestrator.py
python query_database.py --full
```

### Continuous background crawling:
```bash
python orchestrator.py --scheduled &
```

### Monitor while running:
```bash
watch "sqlite3 findings.db 'SELECT COUNT(*) FROM findings;'"
```

---

**Created:** March 2026
**Status:** Production-ready automation framework
