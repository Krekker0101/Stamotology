"""
Helper utilities for Laboratory Management System
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import shutil


logger = logging.getLogger(__name__)


def format_phone_number(phone: str) -> str:
    """Format phone number for display"""
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 11 and digits.startswith('8'):
        # Russian format: 8 (XXX) XXX-XX-XX
        return f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif len(digits) == 10:
        # Format: (XXX) XXX-XX-XX
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    else:
        return phone


def validate_phone_number(phone: str) -> bool:
    """Validate phone number"""
    if not phone:
        return False
    
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10


def format_date(date: Optional[datetime], format_str: str = "%d.%m.%Y") -> str:
    """Format datetime for display"""
    if not date:
        return ""
    return date.strftime(format_str)


def format_datetime(date: Optional[datetime], format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Format datetime with time for display"""
    if not date:
        return ""
    return date.strftime(format_str)


def parse_date(date_str: str, format_str: str = "%d.%m.%Y") -> Optional[datetime]:
    """Parse date string to datetime"""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None


def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year"""
    current_year = datetime.now().year
    return current_year - birth_year


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def get_file_extension(file_path: str) -> str:
    """Get file extension from path"""
    return Path(file_path).suffix.lower()


def is_valid_image_file(file_path: str) -> bool:
    """Check if file is a valid image"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
    return get_file_extension(file_path) in image_extensions


def is_valid_pdf_file(file_path: str) -> bool:
    """Check if file is a valid PDF"""
    return get_file_extension(file_path) == '.pdf'


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def copy_file_with_unique_name(src: Path, dst_dir: Path) -> Path:
    """Copy file to destination with unique name if file exists"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    dst_path = dst_dir / src.name
    counter = 1
    
    while dst_path.exists():
        stem = src.stem
        suffix = src.suffix
        dst_path = dst_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    shutil.copy2(src, dst_path)
    return dst_path


def delete_file_safely(file_path: Path) -> bool:
    """Safely delete a file"""
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - len(suffix)] + suffix


def generate_backup_filename() -> str:
    """Generate backup filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}.zip"


def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper


def safe_int(value, default: int = 0) -> int:
    """Safely convert value to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default: str = "") -> str:
    """Safely convert value to str"""
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def get_unique_disease_types() -> list:
    """Get list of unique disease types from database"""
    try:
        from database import db_manager
        from models import Patient
        
        with db_manager.session_scope() as session:
            types = session.query(Patient.disease_type).distinct().all()
            return [t[0] for t in types if t[0]]
    except Exception as e:
        logger.error(f"Error getting disease types: {e}")
        return []


def get_unique_doctors() -> list:
    """Get list of unique doctors from database"""
    try:
        from database import db_manager
        from models import Patient
        
        with db_manager.session_scope() as session:
            doctors = session.query(Patient.treating_doctor).distinct().filter(
                Patient.treating_doctor.isnot(None)
            ).all()
            return [d[0] for d in doctors if d[0]]
    except Exception as e:
        logger.error(f"Error getting doctors: {e}")
        return []
