# Dark Web OSINT System - Operations & Deployment Guide

## 📦 System Components Overview

Your enhanced OSINT system now includes:

### Core Components ✅
- **Logging System** (`logging_config.py`) - Structured JSON logging with rotation
- **Alert Manager** (`alerts.py`) - Email alerts with deduplication
- **Health Monitor** (`health_monitor.py`) - Real-time system health tracking
- **False Positive Filter** (`false_positive_filter.py`) - Reduce alert noise
- **Backup Manager** (`backup.py`) - Automated database backups & recovery
- **Query/Export Tools** (`query_database.py`) - CSV export functionality
- **Daemon** (`daemon.py`) - Background service for continuous monitoring

---

## 🚀 Quick Start

### 1. Install New Dependencies
```bash
pip install psutil
```

### 2. Enable Alerts (Optional)
Edit `config.json` and configure SMTP:
```json
"alerts": {
  "enabled": true,
  "smtp": {
    "enabled": true,
    "server": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "sender_email": "osint-alerts@company.com"
  },
  "recipient_email": "security@company.com",
  "risk_thresholds": {
    "critical": 85,
    "high": 70,
    "medium": 50
  }
}
```

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Generate "App Password": https://myaccount.google.com/apppasswords
3. Use the generated password in config

### 3. Start Background Daemon
```bash
# Start daemon
python daemon.py --start

# Check status
python daemon.py --status

# Stop daemon
python daemon.py --stop
```

---

## 📊 New Capabilities

### Logging
All events are logged to `logs/` directory with automatic rotation:
- **File**: `logs/osint_system.log`
- **Format**: JSON for easy parsing
- **Retention**: 10 files × 10MB each

#### Log Examples
```json
{
  "timestamp": "2024-04-14T15:30:45.123456",
  "level": "INFO",
  "logger": "osint_system",
  "message": "EVENT: crawl_attempt",
  "extra_fields": {
    "event_type": "crawl_attempt",
    "url": "http://example.onion",
    "status": "success",
    "duration_ms": 2340
  }
}
```

### Alerts
- **Deduplication**: No duplicate alerts within 24 hours
- **Risk-based**: threshold configurable (0-100)
- **Smart filtering**: Whitelist patterns to reduce noise
- **Email delivery**: SMTP with error handling

#### Send Alert Manually
```python
from alerts import alert_manager
from alerts import alert_manager

finding = {
    'id': 1,
    'url': 'http://example.onion',
    'keyword': 'password',
    'snippet': 'admin password database...',
    'confidence': 0.95,
    'risk_score': 85,
    'classification': 'credential_leak'
}

result = alert_manager.send_alert(finding, 'high')
print(result)
```

### Health Monitoring
Check system health anytime:
```bash
python -c "from health_monitor import health_monitor; print(health_monitor.get_health_report())"
```

Output:
```
╔════════════════════════════════════════════════════════════════╗
║           DARK WEB OSINT SYSTEM HEALTH REPORT                  ║
╚════════════════════════════════════════════════════════════════╝

SYSTEM STATUS: HEALTHY
Report Generated: 2024-04-14T15:30:45.123456

─────────────────────────────────────────────────────────────────
DATABASE
─────────────────────────────────────────────────────────────────
Status: healthy
Size: 45.23MB
Total Findings: 1250
Total Crawls: 342
Last Crawl: 2024-04-14T15:25:00.000000

─────────────────────────────────────────────────────────────────
CRAWLING PERFORMANCE
─────────────────────────────────────────────────────────────────
Success Rate: 94.12%
Avg Duration: 2340ms

─────────────────────────────────────────────────────────────────
TOR CONNECTION
─────────────────────────────────────────────────────────────────
Status: ✓ Connected
```

### False Positive Filtering
Reduce alert noise with whitelisting:

```python
from false_positive_filter import fp_filter

# Check if finding should be filtered
should_filter, reason = fp_filter.should_filter({
    'url': 'http://docs.example.onion',
    'keyword': 'password',
    'snippet': '[example only] password: test123'
})
print(f"Filter: {should_filter}, Reason: {reason}")

# Add patterns to whitelist
fp_filter.add_whitelist_url('github.com/examples')
fp_filter.add_whitelist_keyword('documentation')

# Remove from whitelist
fp_filter.remove_whitelist_url('github.com/examples')

# Check stats
print(fp_filter.get_whitelist_stats())
```

### Backups
Automated daily backup at 3 AM, manual backup anytime:

```python
from backup import backup_manager

# Create backup
result = backup_manager.create_backup(compress=True, tag='manual')
print(f"Backup created: {result['backup_file']}")

# List backups
backups = backup_manager.list_backups()
for b in backups:
    print(f"{b['filename']}: {b['size_mb']}MB")

# Restore from backup
restore = backup_manager.restore_backup('backups/findings_backup_20240414_153000.db.gz')

# Cleanup old backups
cleanup = backup_manager.cleanup_old_backups(retention_days=30)
print(f"Deleted {cleanup['deleted_count']} old backups")

# Get stats
stats = backup_manager.get_backup_stats()
```

### CSV Exports
Export findings for reporting and external analysis:

```bash
# Export individual datasets
python query_database.py --export-findings findings.csv
python query_database.py --export-extracted extracted.csv
python query_database.py --export-risk risk.csv
python query_database.py --export-crawls crawls.csv

# Export everything to a directory
python query_database.py --export-all osint_report_20240414

# Files will be created:
# osint_report_20240414/
# ├── findings.csv
# ├── extracted_data.csv
# ├── risk_assessment.csv
# └── crawl_history.csv
```

CSV output is compatible with:
- Excel / Sheets
- Pandas / R analysis
- SIEM ingestion
- Tableau / BI tools

---

## 🐧 Linux Deployment (systemd)

### Setup
1. Copy project to `/opt/darkweb-osint`
2. Create dedicated user:
   ```bash
   sudo useradd -r -s /bin/bash osint
   sudo chown -R osint:osint /opt/darkweb-osint
   ```

3. Install systemd service:
   ```bash
   sudo cp osint-daemon.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable osint-daemon.service
   ```

### Operations
```bash
# Start the service
sudo systemctl start osint-daemon

# Check status
sudo systemctl status osint-daemon

# View logs
sudo journalctl -u osint-daemon -f

# Stop the service
sudo systemctl stop osint-daemon

# Restart
sudo systemctl restart osint-daemon
```

---

## 🪟 Windows Deployment

### Prerequisites
Download and install nssm (Non-Sucking Service Manager):
- Download: https://nssm.cc/download
- Extract to `C:\Program Files\nssm\`
- Add to PATH

### Setup
```batch
# Run as Administrator
cd C:\path\to\darkweb-osint
osint-service.bat install
```

### Operations
```batch
# Start service
osint-service.bat start

# Check status
osint-service.bat status

# Stop service
osint-service.bat stop

# Remove service
osint-service.bat remove

# View logs
type logs\stdout.log
type logs\stderr.log
```

---

## 🔔 Alert Configuration Examples

### Email Provider Settings

**Gmail:**
```json
"smtp": {
  "server": "smtp.gmail.com",
  "port": 587,
  "use_tls": true
}
```

**Microsoft 365:**
```json
"smtp": {
  "server": "smtp.office365.com",
  "port": 587,
  "use_tls": true
}
```

**Sendgrid:**
```json
"smtp": {
  "server": "smtp.sendgrid.net",
  "port": 587,
  "use_tls": true,
  "username": "apikey"
}
```

### Risk Threshold Customization
```json
"risk_thresholds": {
  "critical": 85,    // Alert on scores 85-100
  "high": 70,        // Alert on scores 70-84
  "medium": 50,      // Alert on scores 50-69
  "low": 0           // Log only, no alert
}
```

---

## 📋 Monitoring Checklist

### Daily
- [ ] Check daemon status: `python daemon.py --status`
- [ ] Review logs: `tail -f logs/osint_system.log`
- [ ] Verify crawl success rate > 90%

### Weekly
- [ ] Export weekly report: `python query_database.py --export-all`
- [ ] Review top findings
- [ ] Check database size and backup count
- [ ] Verify alert delivery

### Monthly
- [ ] Review false positive whitelist accuracy
- [ ] Update keyword list based on findings
- [ ] Audit access logs for security review
- [ ] Backup audit: `backup_manager.get_backup_stats()`

---

## 🚨 Troubleshooting

### Alerts Not Sending
1. Check SMTP config: `grep -A 5 '"smtp"' config.json`
2. Test connectivity: 
   ```bash
   python -c "import smtplib; s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); print('OK')"
   ```
3. Check logs: `grep "Exception\|SMTP" logs/osint_system.log`

### Daemon Not Starting
1. Check PID file: `ls -la osint_daemon.pid`
2. Remove stale PID: `python daemon.py --force-stop`
3. Check logs: `tail -f logs/osint_system.log`

### Low Crawl Success Rate
1. Check Tor: `python daemon.py --status` (see TOR CONNECTION)
2. Verify network: `ping 8.8.8.8`
3. Increase timeouts in config.json: increase `"timeout": 60`

### Database Growing Too Fast
1. Check findings count: `python query_database.py --stats`
2. Reduce keyword frequency (less crawls)
3. Enable aggressive deduplication in enhanced_database.py
4. Archive old findings to separate database

---

## 📚 API Usage Examples

### Custom Integration
```python
from logging_config import get_logger
from alerts import alert_manager
from health_monitor import health_monitor
from false_positive_filter import fp_filter
from backup import backup_manager

# Get logger for your module
logger = get_logger('my_integration')

# Log important events
logger.log_event('custom_event', user='analyst', action='reviewed_finding')

# Send alert programmatically
finding = {...}
alert_manager.send_alert(finding, 'high')

# Check health before operation
if health_monitor.get_system_health()['status'] != 'healthy':
    logger.warning("System not healthy, delaying operation")

# Filter before storing
if not fp_filter.should_filter(finding)[0]:
    # Store finding
    pass

# Backup before major operation
backup_manager.create_backup(tag='pre_operation')
```

---

## 📞 Support

For issues or questions:
1. Check logs: `logs/osint_system.log`
2. Review config: `config.json`
3. Run health check: `python daemon.py --status`

---

Generated: April 14, 2026
Project: Dark Web OSINT Monitoring System
