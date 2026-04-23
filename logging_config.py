                      
"""
Structured Logging System for Dark Web OSINT
Provides JSON-formatted logs, file rotation, and audit trails
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
                                       
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
                                                              
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

class OSINTLogger:
    """Centralized logger for OSINT system"""
    
    def __init__(self, name, log_dir="logs"):
        """
        Initialize logger with file rotation and structured format
        
        Args:
            name: Logger name (typically __name__)
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
                                                          
        self.logger.handlers.clear()
        
                                                              
        log_file = self.log_dir / f"{name.replace('.', '_')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,        
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(file_handler)
        
                                                     
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message, **extra_fields):
        """Log debug message"""
        self._log_with_extra(logging.DEBUG, message, extra_fields)
    
    def info(self, message, **extra_fields):
        """Log info message"""
        self._log_with_extra(logging.INFO, message, extra_fields)
    
    def warning(self, message, **extra_fields):
        """Log warning message"""
        self._log_with_extra(logging.WARNING, message, extra_fields)
    
    def error(self, message, **extra_fields):
        """Log error message"""
        self._log_with_extra(logging.ERROR, message, extra_fields)
    
    def critical(self, message, **extra_fields):
        """Log critical message"""
        self._log_with_extra(logging.CRITICAL, message, extra_fields)
    
    def _log_with_extra(self, level, message, extra_fields):
        """Internal method to log with extra fields"""
        if extra_fields:
            extra = {'extra_fields': extra_fields}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)
    
    def log_event(self, event_type, **details):
        """Log structured event (recommended for important events)"""
        event_data = {
            'event_type': event_type,
            **details
        }
        self.info(f"EVENT: {event_type}", **event_data)
    
    def log_crawl_attempt(self, url, status, duration_ms=None, error=None):
        """Log a crawl attempt"""
        self.log_event(
            'crawl_attempt',
            url=url,
            status=status,
            duration_ms=duration_ms,
            error=error
        )
    
    def log_finding(self, url, keyword, confidence, risk_score, snippet=None):
        """Log a finding"""
        self.log_event(
            'finding_discovered',
            url=url,
            keyword=keyword,
            confidence=confidence,
            risk_score=risk_score,
            snippet=snippet
        )
    
    def log_alert(self, finding_id, risk_level, recipient, status):
        """Log alert sent"""
        self.log_event(
            'alert_sent',
            finding_id=finding_id,
            risk_level=risk_level,
            recipient=recipient,
            status=status
        )
    
    def log_error_with_context(self, error_message, context_dict):
        """Log error with full context"""
        self.error(error_message, **context_dict)

                                  
logger = OSINTLogger('osint_system')

def get_logger(name):
    """Factory function to create loggers for specific modules"""
    return OSINTLogger(name)
