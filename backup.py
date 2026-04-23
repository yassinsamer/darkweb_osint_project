                      
"""
Database Backup Manager for Dark Web OSINT
Handles automated backups with compression and rotation
"""

import sqlite3
import shutil
import os
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from logging_config import get_logger

logger = get_logger(__name__)

class BackupManager:
    """Manages database backups and retention"""
    
    def __init__(self, db_path="findings.db", backup_dir="backups", config_path="config.json"):
        """
        Initialize backup manager
        
        Args:
            db_path: Path to main database file
            backup_dir: Directory for backups
            config_path: Path to config.json
        """
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.config_path = config_path
        self.config = self._load_config()
        self.retention_days = 30                     
        self.compression_enabled = True
    
    def _load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def create_backup(self, compress=True, tag=None):
        """
        Create a backup of the database
        
        Args:
            compress: Whether to compress with gzip
            tag: Optional tag for backup (e.g., 'manual', 'scheduled')
        
        Returns:
            dict: Backup operation result
        """
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Database not found: {self.db_path}")
                return {
                    'success': False,
                    'error': 'Database file not found'
                }
            
                                      
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            tag_str = f"_{tag}" if tag else ""
            backup_name = f"findings_backup_{timestamp}{tag_str}"
            
                                                    
            backup_path = self.backup_dir / f"{backup_name}.db"
            
            logger.info(f"Creating backup: {backup_path}")
            
                                                                
            shutil.copy2(self.db_path, str(backup_path))
            
                                   
            if compress:
                compressed_path = self.backup_dir / f"{backup_name}.db.gz"
                self._compress_backup(str(backup_path), str(compressed_path))
                os.remove(backup_path)                       
                backup_path = compressed_path
            
            backup_size_mb = os.path.getsize(backup_path) / (1024*1024)
            
            logger.log_event(
                'backup_created',
                backup_file=str(backup_path),
                size_mb=round(backup_size_mb, 2),
                compressed=compress
            )
            
            return {
                'success': True,
                'backup_file': str(backup_path),
                'size_mb': round(backup_size_mb, 2),
                'timestamp': timestamp,
                'compressed': compress
            }
        
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _compress_backup(self, source, destination):
        """Compress backup file using gzip"""
        try:
            with open(source, 'rb') as f_in:
                with gzip.open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"Backup compressed: {destination}")
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise
    
    def restore_backup(self, backup_file):
        """
        Restore from a backup
        
        Args:
            backup_file: Path to backup file
        
        Returns:
            dict: Restore operation result
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }
            
                                 
            is_compressed = str(backup_file).endswith('.gz')
            
            if is_compressed:
                                                  
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name
                
                with gzip.open(str(backup_path), 'rb') as f_in:
                    with open(tmp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                source_path = tmp_path
            else:
                source_path = str(backup_path)
            
                                    
            try:
                conn = sqlite3.connect(source_path)
                conn.execute("SELECT 1 FROM findings LIMIT 1")
                conn.close()
            except Exception as e:
                logger.error(f"Backup integrity check failed: {e}")
                return {
                    'success': False,
                    'error': 'Backup file is corrupted'
                }
            
                                                      
            safety_backup = self.create_backup(tag="pre_restore")
            
                     
            shutil.copy2(source_path, self.db_path)
            
                                                     
            if is_compressed:
                os.remove(tmp_path)
            
            logger.log_event(
                'backup_restored',
                backup_file=str(backup_path),
                safety_backup=safety_backup
            )
            
            return {
                'success': True,
                'restored_file': self.db_path,
                'safety_backup': safety_backup.get('backup_file'),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_backups(self, retention_days=None):
        """
        Delete old backups beyond retention period
        
        Args:
            retention_days: Days to keep backups (uses config default if None)
        
        Returns:
            dict: Cleanup result
        """
        if retention_days is None:
            retention_days = self.retention_days
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = 0
            freed_mb = 0
            
            for backup_file in self.backup_dir.glob("findings_backup_*"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    file_size_mb = backup_file.stat().st_size / (1024*1024)
                    backup_file.unlink()
                    deleted_count += 1
                    freed_mb += file_size_mb
                    logger.info(f"Deleted old backup: {backup_file.name}")
            
            logger.log_event(
                'backups_cleaned',
                deleted_count=deleted_count,
                freed_mb=round(freed_mb, 2),
                retention_days=retention_days
            )
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'freed_mb': round(freed_mb, 2)
            }
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self):
        """
        List all available backups
        
        Returns:
            list: Backup file information
        """
        try:
            backups = []
            for backup_file in sorted(self.backup_dir.glob("findings_backup_*"), reverse=True):
                file_size_mb = backup_file.stat().st_size / (1024*1024)
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': round(file_size_mb, 2),
                    'created': file_time.isoformat(),
                    'compressed': backup_file.name.endswith('.gz')
                })
            
            return backups
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def get_backup_stats(self):
        """Get backup statistics"""
        try:
            backups = self.list_backups()
            total_size_mb = sum(b['size_mb'] for b in backups)
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size_mb, 2),
                'oldest_backup': backups[-1]['created'] if backups else None,
                'newest_backup': backups[0]['created'] if backups else None,
                'retention_days': self.retention_days
            }
        
        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return {}

                           
backup_manager = BackupManager()
