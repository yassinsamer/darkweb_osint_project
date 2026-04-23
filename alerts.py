#!/usr/bin/env python3
"""
Alert Manager for Dark Web OSINT
Sends Telegram alerts for high-risk findings with deduplication
"""

import hashlib
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from logging_config import get_logger

logger = get_logger(__name__)


class AlertManager:
    """Manages alert deduplication and Telegram delivery"""
    
    def __init__(self, config_path="config.json"):
        """
        Initialize alert manager
        
        Args:
            config_path: Path to config.json
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.alert_db = "alert_history.db"
        self._init_alert_db()
    
    def _load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _init_alert_db(self):
        """Initialize alert deduplication database"""
        conn = sqlite3.connect(self.alert_db)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_hash TEXT UNIQUE,
                finding_id INTEGER,
                risk_level TEXT,
                first_alert_time TIMESTAMP,
                last_alert_time TIMESTAMP,
                alert_count INTEGER DEFAULT 1,
                recipient TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _get_finding_hash(self, url, keyword, snippet=None):
        """Generate hash for deduplication"""
        content = f"{url}:{keyword}:{snippet or ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_duplicate(self, url, keyword, snippet=None, dedupe_window_hours=24):
        """
        Check if finding was already alerted on recently
        
        Args:
            url: Source URL
            keyword: Matched keyword
            snippet: Text snippet (optional)
            dedupe_window_hours: Hours to consider as "recent"
        
        Returns:
            bool: True if duplicate (already alerted), False if new
        """
        finding_hash = self._get_finding_hash(url, keyword, snippet)
        
        conn = sqlite3.connect(self.alert_db)
        c = conn.cursor()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=dedupe_window_hours)
        c.execute("""
            SELECT last_alert_time, alert_count FROM alert_history
            WHERE finding_hash = ? AND last_alert_time > ?
        """, (finding_hash, cutoff_time.isoformat()))
        
        result = c.fetchone()
        conn.close()
        
        return result is not None
    
    def send_alert(self, finding, risk_level, chat_id=None):
        """
        Send Telegram alert for high-risk finding

        Args:
            finding: Finding dict with keys: id, url, keyword, confidence,
                    risk_score, snippet, classification
            risk_level: 'critical', 'high', 'medium'
            chat_id: Telegram chat ID (uses config default if None)

        Returns:
            dict: {'sent': bool, 'chat_id': str, 'timestamp': str, 'message': str}
        """
        # Check for duplicate
        if self.is_duplicate(finding.get('url'), finding.get('keyword'),
                           finding.get('snippet')):
            logger.info(
                "Alert suppressed (duplicate)",
                url=finding.get('url'),
                keyword=finding.get('keyword')
            )
            return {
                'sent': False,
                'message': 'Duplicate (already alerted recently)',
                'suppressed': True
            }

        try:
            # Send Telegram alert
            telegram_result = self._send_telegram_alert(finding, risk_level, chat_id)
            if telegram_result['sent']:
                # Record alert
                self._record_alert(finding, risk_level, chat_id)
                logger.log_alert(
                    finding.get('id'),
                    risk_level,
                    chat_id,
                    "sent_via_telegram"
                )
                return {
                    'sent': True,
                    'chat_id': telegram_result['chat_id'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'sent': False,
                    'message': f"Telegram delivery failed: {telegram_result.get('message', 'Unknown error')}"
                }

        except Exception as e:
            logger.error(f"Alert send exception: {e}", finding_id=finding.get('id'))
            return {
                'sent': False,
                'message': str(e)
            }
    
    def _send_telegram_alert(self, finding, risk_level, chat_id=None):
        """Send Telegram alert"""
        # Use configured chat ID if not provided
        if not chat_id:
            chat_id = self.config.get('alerts', {}).get('telegram', {}).get('chat_id')

        if not chat_id:
            return {'sent': False, 'message': 'No Telegram chat ID configured'}

        try:
            # Build Telegram message
            message = self._build_telegram_message(finding, risk_level)

            # Send via Telegram
            success = self._send_telegram_message(chat_id, message)

            if success:
                return {'sent': True, 'chat_id': chat_id}
            else:
                return {'sent': False, 'message': 'Telegram API delivery failed'}

        except Exception as e:
            logger.error(f"Telegram alert exception: {e}")
            return {'sent': False, 'message': str(e)}
    def _build_telegram_message(self, finding, risk_level):
        """Build formatted Telegram message"""
        risk_emojis = {
            'critical': '🔴 CRITICAL',
            'high': '🟠 HIGH',
            'medium': '🟡 MEDIUM',
            'low': '🟢 LOW'
        }

        emoji = risk_emojis.get(risk_level.lower(), risk_level)

        message = f"""
🚨 *DARK WEB OSINT ALERT*
{emoji}

🔍 *Finding Details:*
• Keyword: `{finding.get('keyword')}`
• Source: `{finding.get('url')}`
• Risk Score: `{finding.get('risk_score', 'N/A')}/100`
• Confidence: `{finding.get('confidence', 'N/A')}%`
• Classification: `{finding.get('classification', 'Unknown')}`

📄 *Snippet:*
```
{finding.get('snippet', 'N/A')[:300]}
```

⏰ *Discovered:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

⚠️ *Action Required:*
• Review finding in OSINT dashboard
• Assess business impact
• Follow incident response procedures
• Log in security systems

📞 *Contact:* {self.config.get('alerts', {}).get('contact_email', 'security@company.com')}
        """.strip()

        return message
    
    def _send_telegram_message(self, chat_id, message):
        """Send message via Telegram Bot API"""
        try:
            telegram_config = self.config.get('alerts', {}).get('telegram', {})

            if not telegram_config.get('enabled'):
                logger.info("Telegram alerts disabled in config")
                return False

            bot_token = telegram_config.get('bot_token')
            if not bot_token:
                logger.error("No Telegram bot token configured")
                return False

            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }

            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                logger.info(f"Telegram alert sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram API request error: {e}")
            return False
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def _record_alert(self, finding, risk_level, recipient):
        """Record alert in deduplication database"""
        try:
            finding_hash = self._get_finding_hash(
                finding.get('url'),
                finding.get('keyword'),
                finding.get('snippet')
            )
            
            conn = sqlite3.connect(self.alert_db)
            c = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            # Try to update existing record
            c.execute("""
                UPDATE alert_history
                SET last_alert_time = ?, alert_count = alert_count + 1
                WHERE finding_hash = ?
            """, (now, finding_hash))
            
            if c.rowcount == 0:
                # Insert new record
                c.execute("""
                    INSERT INTO alert_history
                    (finding_hash, finding_id, risk_level, first_alert_time, 
                     last_alert_time, recipient)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (finding_hash, finding.get('id'), risk_level, now, now, recipient))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Failed to record alert: {e}")
    
    def get_alert_stats(self):
        """Get alert statistics"""
        try:
            conn = sqlite3.connect(self.alert_db)
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM alert_history")
            total_alerts = c.fetchone()[0]
            
            c.execute("""
                SELECT risk_level, COUNT(*) 
                FROM alert_history 
                GROUP BY risk_level
            """)
            by_risk = dict(c.fetchall())
            
            c.execute("""
                SELECT COUNT(DISTINCT recipient) 
                FROM alert_history
            """)
            unique_recipients = c.fetchone()[0]
            
            conn.close()
            
            return {
                'total_alerts': total_alerts,
                'by_risk_level': by_risk,
                'unique_recipients': unique_recipients
            }
        
        except Exception as e:
            logger.error(f"Failed to get alert stats: {e}")
            return {}

    def test_telegram_connection(self):
        """Test Telegram bot connection"""
        try:
            telegram_config = self.config.get('alerts', {}).get('telegram', {})
            bot_token = telegram_config.get('bot_token')
            chat_id = telegram_config.get('chat_id')

            if not bot_token or not chat_id:
                return {'success': False, 'message': 'Bot token or chat ID not configured'}

            api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            bot_info = response.json()
            if bot_info.get('ok'):
                # Test sending a message
                test_message = "🧪 *OSINT Alert System Test*\n\n✅ Telegram integration working!\n⏰ " + datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

                api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': test_message,
                    'parse_mode': 'Markdown'
                }

                response = requests.post(api_url, json=payload, timeout=10)
                response.raise_for_status()

                result = response.json()
                if result.get('ok'):
                    return {
                        'success': True,
                        'bot_username': bot_info['result']['username'],
                        'message': 'Test message sent successfully'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Failed to send test message: {result.get("description")}'
                    }
            else:
                return {'success': False, 'message': 'Invalid bot token'}

        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'Network error: {e}'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {e}'}


# Export singleton instance
alert_manager = AlertManager()
