"""
Backup service for Laboratory Management System
Handles database backup and restore operations
"""
import shutil
import logging
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Tuple, List
import config
from database import db_manager


logger = logging.getLogger(__name__)


class BackupService:
    """Backup service class"""
    
    @staticmethod
    def create_backup() -> Tuple[bool, str, str]:
        """
        Создать резервную копию базы данных и файлов
        
        Returns:
            Tuple of (success, message, backup_path)
        """
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.zip"
            backup_path = config.config.BACKUP_DIR / backup_name
            
            # Create temporary directory for backup
            temp_dir = config.config.BACKUP_DIR / f"temp_{timestamp}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Copy database file
                if config.config.DB_PATH.exists():
                    shutil.copy2(config.config.DB_PATH, temp_dir / config.config.DB_NAME)
                    logger.info(f"Database copied to {temp_dir / config.config.DB_NAME}")
                
                # Copy files directory
                if config.config.FILES_DIR.exists():
                    shutil.copytree(config.config.FILES_DIR, temp_dir / "files")
                    logger.info(f"Files directory copied to {temp_dir / 'files'}")
                
                # Create zip archive
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)
                
                logger.info(f"Backup created successfully: {backup_path}")
                
                # Clean up old backups if needed
                BackupService._cleanup_old_backups()
                
                return True, "Резервная копия создана успешно", str(backup_path)
                
            finally:
                # Clean up temporary directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, f"Ошибка создания резервной копии: {str(e)}", ""
    
    @staticmethod
    def restore_backup(backup_path: str) -> Tuple[bool, str]:
        """
        Восстановить базу данных и файлы из резервной копии
        
        Args:
            backup_path: Путь к zip файлу резервной копии
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, "Файл резервной копии не найден"
            
            # Create temporary directory for extraction
            temp_dir = config.config.BACKUP_DIR / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Extract backup
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                logger.info(f"Backup extracted to {temp_dir}")
                
                # Close database connection before restore
                db_manager.close()
                
                # Restore database
                db_backup = temp_dir / config.config.DB_NAME
                if db_backup.exists():
                    # Backup current database
                    if config.config.DB_PATH.exists():
                        current_backup = config.config.DB_PATH.with_suffix('.bak')
                        shutil.copy2(config.config.DB_PATH, current_backup)
                        logger.info(f"Current database backed up to {current_backup}")
                    
                    # Restore database
                    shutil.copy2(db_backup, config.config.DB_PATH)
                    logger.info(f"Database restored from {db_backup}")
                
                # Restore files
                files_backup = temp_dir / "files"
                if files_backup.exists():
                    # Backup current files
                    if config.config.FILES_DIR.exists():
                        current_files_backup = config.config.FILES_DIR.with_suffix('.bak')
                        if current_files_backup.exists():
                            shutil.rmtree(current_files_backup)
                        shutil.copytree(config.config.FILES_DIR, current_files_backup)
                        logger.info(f"Current files backed up to {current_files_backup}")
                    
                    # Restore files
                    if config.config.FILES_DIR.exists():
                        shutil.rmtree(config.config.FILES_DIR)
                    shutil.copytree(files_backup, config.config.FILES_DIR)
                    logger.info(f"Files restored from {files_backup}")
                
                # Reinitialize database connection
                db_manager._initialize_database()
                
                return True, "Резервная копия восстановлена успешно"
                
            except Exception as e:
                # Try to restore from backup if restore failed
                logger.error(f"Restore failed, attempting to recover: {e}")
                current_backup = config.config.DB_PATH.with_suffix('.bak')
                if current_backup.exists():
                    shutil.copy2(current_backup, config.config.DB_PATH)
                    logger.info("Recovered from pre-restore backup")
                raise
                
            finally:
                # Clean up temporary directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, f"Ошибка восстановления резервной копии: {str(e)}"
    
    @staticmethod
    def get_backup_list() -> List[dict]:
        """
        Получить список доступных резервных копий
        
        Returns:
            Список словарей с информацией о резервных копиях
        """
        try:
            backups = []
            
            if not config.config.BACKUP_DIR.exists():
                return backups
            
            for backup_file in config.config.BACKUP_DIR.glob("backup_*.zip"):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
            
            # Sort by creation date, newest first
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            return []
    
    @staticmethod
    def delete_backup(backup_path: str) -> Tuple[bool, str]:
        """
        Удалить файл резервной копии
        
        Args:
            backup_path: Путь к файлу резервной копии
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, "Файл резервной копии не найден"
            
            # Verify it's in the backup directory
            if not str(backup_file).startswith(str(config.config.BACKUP_DIR)):
                return False, "Невозможно удалить файл вне директории резервных копий"
            
            backup_file.unlink()
            logger.info(f"Backup deleted: {backup_path}")
            
            return True, "Резервная копия удалена успешно"
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False, f"Ошибка удаления резервной копии: {str(e)}"
    
    @staticmethod
    def _cleanup_old_backups():
        """Удалить старые резервные копии если превышен лимит"""
        try:
            backups = BackupService.get_backup_list()
            
            if len(backups) > config.config.MAX_BACKUPS:
                # Remove oldest backups
                backups_to_delete = backups[config.config.MAX_BACKUPS:]
                
                for backup_info in backups_to_delete:
                    backup_path = Path(backup_info['path'])
                    if backup_path.exists():
                        backup_path.unlink()
                        logger.info(f"Old backup deleted: {backup_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    @staticmethod
    def get_backup_size() -> int:
        """Get total size of all backups in bytes"""
        try:
            total_size = 0
            
            if not config.config.BACKUP_DIR.exists():
                return 0
            
            for backup_file in config.config.BACKUP_DIR.glob("backup_*.zip"):
                total_size += backup_file.stat().st_size
            
            return total_size
            
        except Exception as e:
            logger.error(f"Error calculating backup size: {e}")
            return 0


# Global backup service instance
backup_service = BackupService()
