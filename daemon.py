#!/usr/bin/env python3
"""
Background daemon for continuous Dark Web OSINT monitoring
Runs scheduled crawls periodically
"""

import schedule
import time
import signal
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from logging_config import get_logger
from orchestrator import DarkWebOrchestrator
from backup import backup_manager
from health_monitor import health_monitor

logger = get_logger(__name__)


class OSINTDaemon:
    """Background daemon for OSINT monitoring"""
    
    def __init__(self, config_path="config.json"):
        """Initialize daemon"""
        self.config_path = config_path
        self.config = self._load_config()
        self.orchestrator = DarkWebOrchestrator(config_path)
        self.running = False
        self.pid_file = Path("osint_daemon.pid")
    
    def _load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _is_already_running(self):
        """Check if daemon is already running"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file) as f:
                    pid = int(f.read())
                    # Check if process exists
                    os.kill(pid, 0)
                    return True
            except (OSError, ValueError):
                # Process doesn't exist or pid is invalid
                self.pid_file.unlink(missing_ok=True)
                return False
        return False
    
    def _write_pid(self):
        """Write daemon PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")
    
    def _remove_pid(self):
        """Remove PID file"""
        self.pid_file.unlink(missing_ok=True)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def schedule_jobs(self):
        """Schedule crawling jobs"""
        scheduling = self.config.get('scheduling', {})
        
        if not scheduling.get('enable_scheduler', False):
            logger.warning("Scheduling is disabled in config")
            return
        
        interval_minutes = scheduling.get('interval_minutes', 60)
        start_hour = scheduling.get('start_hour', 0)
        end_hour = scheduling.get('end_hour', 23)
        
        def run_if_in_window():
            """Only run if within scheduled hours"""
            current_hour = datetime.now().hour
            if start_hour <= current_hour <= end_hour:
                self._run_crawl_cycle()
            else:
                logger.debug(f"Outside crawl window (current hour: {current_hour})")
        
        # Schedule periodic crawls
        schedule.every(interval_minutes).minutes.do(run_if_in_window)
        
        # Schedule daily backup at 3 AM
        schedule.every().day.at("03:00").do(self._run_backup)
        
        # Schedule health check every 30 minutes
        schedule.every(30).minutes.do(self._check_health)
        
        logger.info(f"Scheduled jobs configured:")
        logger.info(f"  - Crawl cycle every {interval_minutes} minutes")
        logger.info(f"  - Daily backup at 03:00")
        logger.info(f"  - Health check every 30 minutes")
        logger.info(f"  - Active window: {start_hour}:00 - {end_hour}:59")
    
    def _run_crawl_cycle(self):
        """Run full crawl cycle"""
        try:
            logger.log_event('crawl_cycle_started', time=datetime.utcnow().isoformat())
            self.orchestrator.run_full_cycle()
            logger.log_event('crawl_cycle_completed', time=datetime.utcnow().isoformat())
        except Exception as e:
            logger.error(f"Crawl cycle failed: {e}", exception_details=str(e))
    
    def _run_backup(self):
        """Run database backup"""
        try:
            logger.info("Starting scheduled backup...")
            result = backup_manager.create_backup(compress=True, tag='scheduled')
            if result.get('success'):
                logger.log_event(
                    'backup_completed',
                    backup_file=result.get('backup_file'),
                    size_mb=result.get('size_mb')
                )
                # Cleanup old backups
                cleanup = backup_manager.cleanup_old_backups()
                logger.info(f"Cleanup: {cleanup}")
            else:
                logger.error(f"Backup failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def _check_health(self):
        """Check system health and log """
        try:
            health = health_monitor.get_system_health()
            status = health.get('status')
            
            logger.log_event(
                'health_check',
                status=status,
                cpu_percent=health.get('system', {}).get('cpu_percent'),
                success_rate=health.get('crawling', {}).get('success_rate_percent')
            )
            
            if status == 'warning':
                logger.warning("System health warning detected")
            elif status == 'critical':
                logger.critical("System health critical!")
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def start(self):
        """Start the daemon"""
        if self._is_already_running():
            logger.error("Daemon is already running!")
            print("Error: Daemon is already running. Run with --stop to stop it.")
            return False
        
        logger.info("="*60)
        logger.info("Starting Dark Web OSINT Daemon")
        logger.info("="*60)
        
        self._write_pid()
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Schedule jobs
        self.schedule_jobs()
        
        logger.info("Daemon started successfully. Entering job loop...")
        
        # Main loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                time.sleep(60)
        
        self.stop()
    
    def stop(self):
        """Stop the daemon"""
        logger.info("Stopping daemon...")
        self.running = False
        self._remove_pid()
        logger.info("Daemon stopped")
    
    def get_status(self):
        """Check daemon status"""
        if self._is_already_running():
            with open(self.pid_file) as f:
                pid = f.read()
            print(f"✓ Daemon is running (PID: {pid})")
            print(f"\nSystem Health:")
            print(health_monitor.get_health_report())
            return True
        else:
            print("✗ Daemon is not running")
            return False


def main():
    """Main entry point"""
    daemon = OSINTDaemon()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--start":
            daemon.start()
        elif command == "--stop":
            if daemon._is_already_running():
                logger.info("Stopping existing daemon...")
                # In production, would use proper signal handling
                daemon._remove_pid()
                print("Daemon stop signal sent")
            else:
                print("Daemon is not running")
        elif command == "--status":
            daemon.get_status()
        elif command == "--restart":
            if daemon._is_already_running():
                print("Stopping daemon...")
                daemon._remove_pid()
                time.sleep(2)
            print("Starting daemon...")
            daemon.start()
        elif command == "--force-stop":
            daemon._remove_pid()
            print("Daemon PID file removed (force stop)")
        else:
            print("Usage: daemon.py [--start|--stop|--status|--restart|--force-stop]")
    else:
        print("Usage: daemon.py [--start|--stop|--status|--restart|--force-stop]")
        print("\nExample:")
        print("  python daemon.py --start    # Start the daemon")
        print("  python daemon.py --status   # Check daemon status")
        print("  python daemon.py --stop     # Stop the daemon")


if __name__ == "__main__":
    main()
