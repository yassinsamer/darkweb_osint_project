                      
"""
False Positive Filter for Dark Web OSINT
Reduces alert noise through configurable whitelisting
"""

import json
import re
from logging_config import get_logger

logger = get_logger(__name__)

class FalsePositiveFilter:
    """Filters false positives and known non-threats"""
    
    def __init__(self, config_path="config.json"):
        """
        Initialize false positive filter
        
        Args:
            config_path: Path to config.json
        """
        self.config = self._load_config(config_path)
        self.fp_config = self.config.get('false_positives', {})
        self.whitelist_urls = self.fp_config.get('whitelist_urls', [])
        self.whitelist_keywords = self.fp_config.get('whitelist_keywords', [])
        self.common_false_positives = self._build_common_fp_patterns()
    
    def _load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _build_common_fp_patterns(self):
        """Build common false positive patterns"""
        return {
            'generic_emails': [
                r'^admin@.*',
                r'^support@.*',
                r'^noreply@.*',
                r'^test@.*',
                r'^example@example\.com'
            ],
            'test_data': [
                r'test',
                r'demo',
                r'sample',
                r'example'
            ],
            'documentation': [
                r'readme',
                r'documentation',
                r'docs',
                r'guide'
            ]
        }
    
    def should_filter(self, finding):
        """
        Determine if a finding should be filtered (suppressed)
        
        Args:
            finding: Dict with url, keyword, snippet, data_value
        
        Returns:
            tuple: (should_filter: bool, reason: str)
        """
                             
        if self._is_url_whitelisted(finding.get('url')):
            return True, 'URL on whitelist'
        
                                 
        if self._is_keyword_whitelisted(finding.get('keyword')):
            return True, 'Keyword on whitelist'
        
                                      
        if self._is_common_fp(finding):
            reason = self._get_common_fp_reason(finding)
            return True, reason
        
                                                  
        if self._is_false_positive_snippet(finding.get('snippet', '')):
            return True, 'Generic/common snippet pattern'
        
        return False, ''
    
    def _is_url_whitelisted(self, url):
        """Check if URL is in whitelist"""
        if not url:
            return False
        
        for pattern in self.whitelist_urls:
            if pattern.lower() in url.lower():
                logger.debug(f"URL matched whitelist: {url}", pattern=pattern)
                return True
        
        return False
    
    def _is_keyword_whitelisted(self, keyword):
        """Check if keyword is in whitelist"""
        if not keyword:
            return False
        
        for pattern in self.whitelist_keywords:
            if pattern.lower() in keyword.lower():
                logger.debug(f"Keyword matched whitelist: {keyword}", pattern=pattern)
                return True
        
        return False
    
    def _is_common_fp(self, finding):
        """Check if finding matches common false positive patterns"""
        snippet = finding.get('snippet', '').lower()
        data_value = finding.get('data_value', '').lower()
        
                         
        for pattern in self.common_false_positives['test_data']:
            if re.search(pattern, snippet, re.IGNORECASE):
                return True
            if re.search(pattern, data_value, re.IGNORECASE):
                return True
        
                             
        for pattern in self.common_false_positives['documentation']:
            if re.search(pattern, snippet, re.IGNORECASE):
                return True
        
        return False
    
    def _get_common_fp_reason(self, finding):
        """Get reason for false positive classification"""
        snippet = finding.get('snippet', '').lower()
        
        for pattern in self.common_false_positives['test_data']:
            if re.search(pattern, snippet, re.IGNORECASE):
                return 'Test/demo data pattern'
        
        for pattern in self.common_false_positives['documentation']:
            if re.search(pattern, snippet, re.IGNORECASE):
                return 'Documentation pattern'
        
        return 'Common false positive'
    
    def _is_false_positive_snippet(self, snippet):
        """Check if snippet content suggests false positive"""
        if not snippet:
            return False
        
        snippet_lower = snippet.lower()
        
                                                         
        generic_patterns = [
            r'how to|tutorial|guide|documentation',
            r'example\s*only|demo\s*purposes?|test\s*data',
            r'for\s*demonstration|not\s*real|fictional',
            r'\[example\]|\[test\]|\[sample\]',
        ]
        
        for pattern in generic_patterns:
            if re.search(pattern, snippet_lower):
                return True
        
        return False
    
    def add_whitelist_url(self, url_pattern):
        """
        Add URL pattern to whitelist
        
        Args:
            url_pattern: URL pattern to whitelist
        
        Returns:
            bool: True if added, False if already exists
        """
        if url_pattern not in self.whitelist_urls:
            self.whitelist_urls.append(url_pattern)
            self._save_config()
            logger.info(f"Added URL to whitelist: {url_pattern}")
            return True
        return False
    
    def add_whitelist_keyword(self, keyword_pattern):
        """
        Add keyword pattern to whitelist
        
        Args:
            keyword_pattern: Keyword pattern to whitelist
        
        Returns:
            bool: True if added, False if already exists
        """
        if keyword_pattern not in self.whitelist_keywords:
            self.whitelist_keywords.append(keyword_pattern)
            self._save_config()
            logger.info(f"Added keyword to whitelist: {keyword_pattern}")
            return True
        return False
    
    def remove_whitelist_url(self, url_pattern):
        """Remove URL from whitelist"""
        if url_pattern in self.whitelist_urls:
            self.whitelist_urls.remove(url_pattern)
            self._save_config()
            logger.info(f"Removed URL from whitelist: {url_pattern}")
            return True
        return False
    
    def remove_whitelist_keyword(self, keyword_pattern):
        """Remove keyword from whitelist"""
        if keyword_pattern in self.whitelist_keywords:
            self.whitelist_keywords.remove(keyword_pattern)
            self._save_config()
            logger.info(f"Removed keyword from whitelist: {keyword_pattern}")
            return True
        return False
    
    def get_whitelist_stats(self):
        """Get whitelist statistics"""
        return {
            'total_url_patterns': len(self.whitelist_urls),
            'total_keyword_patterns': len(self.whitelist_keywords),
            'url_patterns': self.whitelist_urls,
            'keyword_patterns': self.whitelist_keywords
        }
    
    def _save_config(self):
        """Save updated configuration"""
        try:
            self.fp_config['whitelist_urls'] = self.whitelist_urls
            self.fp_config['whitelist_keywords'] = self.whitelist_keywords
            self.config['false_positives'] = self.fp_config
            
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

                           
fp_filter = FalsePositiveFilter()
