# TOR SETUP & DARK WEB OSINT SYSTEM - COMPLETE GUIDE

## ⚠️ DISCLAIMER
This system is for **AUTHORIZED OSINT RESEARCH ONLY**. Unauthorized access to computer systems is illegal. Ensure you have proper authorization before using this tool.

---

## 🔧 PART 1: INSTALL TOR BROWSER

### Step 1: Download Tor Browser
1. Go to **https://www.torproject.org/download/**
2. Download the Windows version
3. Run the installer and follow the prompts
4. Install to a location like `C:\Tor Browser\`

### Step 2: Configure Tor for SOCKS5 Proxy
The OSINT system needs Tor to run as a SOCKS5 proxy on `127.0.0.1:9150`.

**Option A: Using Tor Browser (Easiest)**
1. Open Tor Browser
2. Click the three-line menu (top right)
3. Go to **Settings** → **Connection**
4. Note the SOCKS port (usually already 9150)
5. Keep Tor Browser **running** while using the OSINT system

**Option B: Using Tor Service (Advanced - Background)**
If you want Tor running without Tor Browser:

1. Download Tor Standalone: **https://www.torproject.org/download/#windows**
2. Extract to `C:\Tor\`
3. Create `C:\Tor\torrc` file with:
```
SocksPort 127.0.0.1:9150
ControlPort 9051
```
4. Run from command line:
```bash
cd C:\Tor\
tor.exe -f torrc
```

---

## 🚀 PART 2: VERIFY TOR CONNECTION

### Check if Tor is running:
```bash
# Test SOCKS5 connection
curl --socks5 127.0.0.1:9150 http://httpbin.org/ip

# If successful, you'll see your Tor exit IP (NOT your real IP)
```

Or use Python to test:
```bash
python test_tor.py
```

---

## 📋 PART 3: CONFIGURE THE OSINT SYSTEM

### Step 1: Edit `config.json`
All settings are in one file - no code changes needed!

**Key settings to review:**

```json
{
  "tor": {
    "proxy": "socks5h://127.0.0.1:9150",    ← Your Tor SOCKS5 address
    "timeout": 60,                           ← Wait max 60s for response
    "retries": 3,                            ← Auto-retry failed requests
    "retry_delay": 5                         ← Wait 5s between retries
  },
  "crawling": {
    "max_workers": 5,                        ← How many parallel crawls
    "batch_size": 10,                        ← URLs per batch
    "delay_between_requests": 2,             ← Respectful delay (seconds)
    "max_page_size_mb": 10                   ← Skip huge pages
  },
  "keywords": [
    "leak",
    "password",
    "email",
    "credit card",
    "ssn"
    // Add your own keywords here
  ],
  "regex_patterns": {
    "email": "...",
    "phone": "...",
    "credit_card": "...",
    "ssn": "...",
    "api_key": "..."
  },
  "seed_urls": [
    "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"
  ],
  "scheduling": {
    "enable_scheduler": true,
    "interval_minutes": 60,                  ← Run every 60 minutes
    "start_hour": 0,                         ← Start at 12 AM
    "end_hour": 23                           ← Stop at 11 PM
  }
}
```

### Step 2: Customize for Your Needs

**Add more keywords:**
```json
"keywords": [
  "leak",
  "password",
  "database",
  "admin",
  "breach",
  "your_target_keyword"  ← Add here
]
```

**Add more seed URLs:**
```json
"seed_urls": [
  "http://url1.onion/",
  "http://url2.onion/",
  "http://url3.onion/"
]
```

**Adjust crawling speed:**
```json
"crawling": {
  "max_workers": 10,              ← Faster (more threads)
  "delay_between_requests": 1     ← Faster (less delay)
}
```

---

## 🏃 PART 4: RUNNING THE SYSTEM

### Prerequisites:
- ✅ Tor Browser running (or Tor service)
- ✅ Dependencies installed: `pip install -r requirements.txt`
- ✅ `config.json` configured

### Option 1: Single Crawl Cycle
Runs once, then shows report:
```bash
python orchestrator.py
```

Output:
- Discovers URLs from Ahmia
- Crawls target pages
- Extracts keywords & patterns
- Shows statistics
- Saves to findings.db

### Option 2: Continuous Background Crawling
Runs forever at intervals (check config.json):
```bash
python orchestrator.py --scheduled
```

Keep this running in a terminal or use:
```bash
# Windows - Run in background
python orchestrator.py --scheduled &

# Or use screen/tmux on Linux
screen -S osint
python orchestrator.py --scheduled
# Detach: Ctrl+A then D
```

---

## 📊 PART 5: ANALYZING FINDINGS

### View Full Report
```bash
python query_database.py --full
```

Shows:
- Keyword frequency
- Top URLs
- Extracted emails/phones/APIs
- Crawl statistics
- Recent findings

### Query Specific Data

**See extracted emails:**
```bash
python query_database.py --extracted
```

**See recent findings:**
```bash
python query_database.py --recent 50
```

**See keyword matches:**
```bash
python query_database.py --keywords
```

**See crawl performance:**
```bash
python query_database.py --stats
```

**See top URLs:**
```bash
python query_database.py --urls
```

### Direct Database Queries
```bash
# Find all extracted emails
sqlite3 findings.db "SELECT DISTINCT data_value FROM extracted_data WHERE data_type='email' LIMIT 10;"

# Find high-confidence keywords
sqlite3 findings.db "SELECT keyword, COUNT(*) FROM findings WHERE confidence_score > 0.8 GROUP BY keyword;"

# See crawl success rate
sqlite3 findings.db "SELECT status, COUNT(*) FROM crawl_history GROUP BY status;"

# Check what URLs were crawled
sqlite3 findings.db "SELECT url, status FROM crawl_history LIMIT 20;"
```

---

## ⚙️ PART 6: TROUBLESHOOTING

### Problem: "Connection refused" error
**Solution:** Start Tor Browser or Tor service
```bash
# Verify Tor is listening
netstat -an | findstr 9150
# Should show: LISTENING on 127.0.0.1:9150
```

### Problem: "Timeout errors"
**Solution:** Increase timeout in config.json
```json
"tor": {
  "timeout": 120  ← Increase from 60 to 120 seconds
}
```

### Problem: "No findings after crawling"
**Solution:** Check if target URLs exist
```bash
# Manually test a URL
python enhanced_crawler.py
# Edit the file and change TARGET_ONION to test
```

### Problem: "Tor IP changed / Tor reconnected"
This is normal - Tor rotates IPs for anonymity. The system handles it automatically.

### Problem: Database errors
**Reset database:**
```bash
Remove-Item findings.db
# Next run will recreate it
python orchestrator.py
```

---

## 🔐 PART 7: SECURITY BEST PRACTICES

### 1. **Always Use VPN + Tor**
```
Internet → VPN → Tor → Target
```

### 2. **Monitor Tor Logs**
Keep Tor Browser open to see connection status and exit nodes

### 3. **Rate Limiting**
```json
"crawling": {
  "delay_between_requests": 5  ← 5s between requests (respectful)
}
```

### 4. **Backup Your Findings**
```bash
# Backup database
cp findings.db findings.db.backup
```

### 5. **Use Different Tor Identities**
Restart Tor Browser to get new exit IP:
```bash
# In Tor Browser: menu → New Identity
```

### 6. **Log Everything**
The system logs all crawls to `crawl_history` table
```bash
sqlite3 findings.db "SELECT * FROM crawl_history;"
```

---

## 📈 PART 8: SCALING UP

### For Faster Crawling:
```json
{
  "crawling": {
    "max_workers": 20,           ← Up from 5
    "delay_between_requests": 1  ← Down from 2
  }
}
```

### For More Keywords:
Add to `config.json`:
```json
"keywords": [
  "leak", "password", "email",
  "credit card", "ssn", "api_key",
  "breach", "hack", "exploit",
  "vulnerability", "admin", "token",
  "database", "username", "secret",
  "private", "confidential", "classified"
]
```

### For More Seed URLs:
Research and add high-value .onion targets:
```json
"seed_urls": [
  "http://ahmia.onion/",
  "http://target1.onion/",
  "http://target2.onion/",
  "http://target3.onion/"
]
```

### For Continuous Monitoring:
Run in separate terminal:
```bash
# Terminal 1: Orchestrator
python orchestrator.py --scheduled

# Terminal 2: Monitor progress
while true { clear; python query_database.py --stats; Start-Sleep 30 }
```

---

## 📝 PART 9: QUICK START CHECKLIST

- [ ] Download and install Tor Browser
- [ ] Start Tor Browser (keep running)
- [ ] Verify Tor with: `curl --socks5 127.0.0.1:9150 http://httpbin.org/ip`
- [ ] Edit `config.json` with your keywords/URLs
- [ ] Run: `python orchestrator.py` (test once)
- [ ] Run: `python orchestrator.py --scheduled` (continuous)
- [ ] Monitor with: `python query_database.py --full`
- [ ] Backup database regularly

---

## 🎯 EXAMPLE WORKFLOW

### Session 1: Setup & Testing
```bash
# Terminal 1: Keep Tor running
# (Tor Browser open)

# Terminal 2: Test once
cd c:\Users\Yassen\Downloads\darkweb_osint_project
python orchestrator.py

# Check results
python query_database.py --recent 10
```

### Session 2: Continuous Crawling
```bash
# Terminal 1: Keep Tor running
# (Tor Browser open)

# Terminal 2: Run continuously
python orchestrator.py --scheduled

# This runs forever, discovering and crawling URLs every 60 min
```

### Session 3: Analyze Findings
```bash
# While orchestrator is running in Terminal 2:
# Terminal 3: Monitor progress

python query_database.py --full    # Full report
python query_database.py --keywords # Top keywords
sqlite3 findings.db "SELECT * FROM extracted_data LIMIT 20;"  # Raw data
```

---

## 🚨 LEGAL WARNING

**This tool should ONLY be used for:**
- ✅ Authorized security research
- ✅ Penetration testing (with written permission)
- ✅ OSINT on public/lawful targets
- ✅ Academic research (approved)

**DO NOT use for:**
- ❌ Unauthorized access to systems
- ❌ Stealing data
- ❌ Privacy violations
- ❌ Any illegal activity

**You are responsible for all activities using this tool.**

---

**Setup Complete!** 🎉

You're now ready to start advanced dark web OSINT operations. Start with `python orchestrator.py` for a test run, then switch to `--scheduled` mode for continuous crawling.
