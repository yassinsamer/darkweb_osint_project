#!/usr/bin/env python3
"""
System Health Monitor for Dark Web OSINT
Tracks crawl performance, database health, and system status
"""

import sqlite3
import os
import psutil
import socket
from datetime import datetime, timedelta
from pathlib import Path
from logging_config import get_logger

logger = get_logger(__name__)


class HealthMonitor:
    """Monitors system health and collects metrics"""
    
    def __init__(self, db_path="findings.db"):
        """Initialize health monitor"""
        self.db_path = db_path
        self.start_time = datetime.utcnow()
    
    def get_system_health(self):
        """
        Get comprehensive system health status
        
        Returns:
            dict: Complete health snapshot
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': self._get_uptime(),
            'database': self._get_database_health(),
            'crawling': self._get_crawling_stats(),
            'system': self._get_system_resources(),
            'status': self._compute_overall_status()
        }
    
    def _get_uptime(self):
        """Get system uptime"""
        try:
            uptime = datetime.utcnow() - self.start_time
            return {
                'started_at': self.start_time.isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_formatted': str(uptime).split('.')[0]
            }
        except Exception as e:
            logger.error(f"Failed to get uptime: {e}")
            return {}
    
    def _get_database_health(self):
        """Get database statistics"""
        try:
            if not os.path.exists(self.db_path):
                return {
                    'status': 'not_found',
                    'database_file': self.db_path
                }
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get table counts
            c.execute("SELECT COUNT(*) FROM findings")
            findings_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM crawl_history")
            crawls_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM url_queue")
            urls_queued = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM extracted_data")
            extracted_count = c.fetchone()[0]
            
            # Get recent activity
            c.execute("""
                SELECT COUNT(*), status FROM crawl_history 
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY status
            """)
            recent = dict(c.fetchall())
            
            # Get last crawl
            c.execute("""
                SELECT created_at, status FROM crawl_history 
                ORDER BY created_at DESC LIMIT 1
            """)
            last_crawl = c.fetchone()
            
            # Get top keywords today
            c.execute("""
                SELECT keyword, COUNT(*) as count 
                FROM findings 
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY keyword 
                ORDER BY count DESC LIMIT 5
            """)
            top_keywords = [{'keyword': row[0], 'count': row[1]} for row in c.fetchall()]
            
            # Get database file size
            db_size_bytes = os.path.getsize(self.db_path)
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            conn.close()
            
            return {
                'status': 'healthy',
                'file_size_mb': round(db_size_mb, 2),
                'file_path': self.db_path,
                'total_findings': findings_count,
                'total_crawls': crawls_count,
                'urls_in_queue': urls_queued,
                'extracted_data_items': extracted_count,
                'findings_last_24h': recent.get('success', 0),
                'last_crawl': {
                    'time': last_crawl[0] if last_crawl else None,
                    'status': last_crawl[1] if last_crawl else None
                },
                'top_keywords_24h': top_keywords
            }
        
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_crawling_stats(self):
        """Get crawling performance statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Success rate (last 100 crawls)
            c.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms
                FROM crawl_history
                ORDER BY created_at DESC
                LIMIT 100
            """)
            
            stats_by_status = {}
            total_crawls = 0
            for status, count, avg_duration in c.fetchall():
                stats_by_status[status] = {
                    'count': count,
                    'avg_duration_ms': avg_duration
                }
                total_crawls += count
            
            success_count = stats_by_status.get('success', {}).get('count', 0)
            success_rate = (success_count / total_crawls * 100) if total_crawls > 0 else 0
            
            # Crawl rate and performance
            c.execute("""
                SELECT 
                    ROUND(AVG(duration_ms), 0) as avg_duration_ms,
                    MIN(duration_ms) as min_duration_ms,
                    MAX(duration_ms) as max_duration_ms
                FROM crawl_history
                WHERE duration_ms IS NOT NULL
            """)
            duration_stats = c.fetchone()
            
            conn.close()
            
            return {
                'success_rate_percent': round(success_rate, 2),
                'recent_crawls_last_100': total_crawls,
                'by_status': stats_by_status,
                'performance': {
                    'avg_duration_ms': duration_stats[0] if duration_stats[0] else 0,
                    'min_duration_ms': duration_stats[1] if duration_stats[1] else 0,
                    'max_duration_ms': duration_stats[2] if duration_stats[2] else 0
                } if duration_stats else {}
            }
        
        except Exception as e:
            logger.error(f"Crawling stats error: {e}")
            return {'error': str(e)}
    
    def _get_system_resources(self):
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'percent': memory.percent,
                    'available_mb': round(memory.available / (1024*1024), 2),
                    'total_mb': round(memory.total / (1024*1024), 2)
                },
                'disk': {
                    'percent': disk.percent,
                    'free_gb': round(disk.free / (1024*1024*1024), 2),
                    'total_gb': round(disk.total / (1024*1024*1024), 2)
                }
            }
        
        except Exception as e:
            logger.error(f"System resources error: {e}")
            return {'error': str(e)}
    
    def _compute_overall_status(self):
        """Compute overall system status"""
        try:
            db_health = self._get_database_health()
            crawl_stats = self._get_crawling_stats()
            system_resources = self._get_system_resources()
            
            # Determine status
            if db_health.get('status') == 'error':
                return 'critical'
            
            success_rate = crawl_stats.get('success_rate_percent', 0)
            if success_rate < 50:
                return 'warning'
            
            cpu = system_resources.get('cpu_percent', 0)
            memory = system_resources.get('memory', {}).get('percent', 0)
            if cpu > 90 or memory > 90:
                return 'warning'
            
            return 'healthy'
        
        except:
            return 'unknown'
    
    def check_tor_connectivity(self, timeout=5):
        """Check if Tor proxy is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex(('127.0.0.1', 9150))
            sock.close()
            
            if result == 0:
                return {
                    'tor_reachable': True,
                    'check_time': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'tor_reachable': False,
                    'error': 'Connection refused on port 9150',
                    'check_time': datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            return {
                'tor_reachable': False,
                'error': str(e),
                'check_time': datetime.utcnow().isoformat()
            }
    
    def get_health_report(self):
        """Get formatted health report"""
        health = self.get_system_health()
        tor_status = self.check_tor_connectivity()
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║           DARK WEB OSINT SYSTEM HEALTH REPORT                  ║
╚════════════════════════════════════════════════════════════════╝

SYSTEM STATUS: {health['status'].upper()}
Report Generated: {health['timestamp']}

─────────────────────────────────────────────────────────────────
UPTIME
─────────────────────────────────────────────────────────────────
Started: {health['uptime'].get('started_at')}
Uptime: {health['uptime'].get('uptime_formatted')}

─────────────────────────────────────────────────────────────────
DATABASE
─────────────────────────────────────────────────────────────────
Status: {health['database'].get('status')}
Size: {health['database'].get('file_size_mb')}MB
Total Findings: {health['database'].get('total_findings')}
Total Crawls: {health['database'].get('total_crawls')}
Queue Depth: {health['database'].get('urls_in_queue')}
Last Crawl: {health['database'].get('last_crawl', {}).get('time')}

─────────────────────────────────────────────────────────────────
CRAWLING PERFORMANCE
─────────────────────────────────────────────────────────────────
Success Rate: {health['crawling'].get('success_rate_percent')}%
Avg Duration: {health['crawling'].get('performance', {}).get('avg_duration_ms')}ms

─────────────────────────────────────────────────────────────────
SYSTEM RESOURCES
─────────────────────────────────────────────────────────────────
CPU: {health['system'].get('cpu_percent')}%
Memory: {health['system'].get('memory', {}).get('percent')}%
Disk: {health['system'].get('disk', {}).get('percent')}%

─────────────────────────────────────────────────────────────────
TOR CONNECTION
─────────────────────────────────────────────────────────────────
Status: {'✓ Connected' if tor_status.get('tor_reachable') else '✗ Disconnected'}
"""
        return report


# Export singleton instance
health_monitor = HealthMonitor()
