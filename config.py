"""
Configuration module for Laboratory Management System
"""
import os
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"


class Language(Enum):
    RUSSIAN = "ru"
    TAJIK = "tg"


class UserRole(Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    RECEPTIONIST = "receptionist"


class TreatmentStatus(Enum):
    IN_PROGRESS = "in_progress"
    CURED = "cured"
    TREATMENT_COMPLETED = "treatment_completed"
    NOT_CURED = "not_cured"
    REFUSED = "refused"
    NO_CHANGE = "no_change"


@dataclass
class AppConfig:
    """Application configuration"""
    
    # Database
    DB_NAME: str = "laboratory.db"
    DB_PATH: Path = Path(__file__).parent / DB_NAME
    
    # Application
    APP_NAME: str = "Laboratory Management System"
    APP_VERSION: str = "1.0.0"
    
    # UI
    WINDOW_WIDTH: int = 1400
    WINDOW_HEIGHT: int = 900
    MIN_WINDOW_WIDTH: int = 1024
    MIN_WINDOW_HEIGHT: int = 768
    
    # Pagination
    PAGE_SIZE: int = 50
    
    # Backup
    BACKUP_DIR: Path = Path(__file__).parent / "backups"
    MAX_BACKUPS: int = 10
    
    # Files
    FILES_DIR: Path = Path(__file__).parent / "files"
    
    # Theme
    DEFAULT_THEME: Theme = Theme.LIGHT
    
    # Language
    DEFAULT_LANGUAGE: Language = Language.RUSSIAN
    current_language: Language = Language.RUSSIAN
    
    # Default credentials (for first run)
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    
    # Logging
    LOG_FILE: Path = Path(__file__).parent / "app.log"
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        """Create necessary directories"""
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.FILES_DIR.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = AppConfig()


def get_theme_colors(theme: Theme) -> dict:
    """Get color scheme for theme"""
    if theme == Theme.LIGHT:
        return {
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "primary": "#2196F3",
            "primary_hover": "#1976D2",
            "text": "#212121",
            "text_secondary": "#757575",
            "border": "#E0E0E0",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "info": "#2196F3",
        }
    else:
        return {
            "background": "#1E1E1E",
            "surface": "#2D2D2D",
            "primary": "#64B5F6",
            "primary_hover": "#42A5F5",
            "text": "#FFFFFF",
            "text_secondary": "#B0B0B0",
            "border": "#404040",
            "success": "#81C784",
            "warning": "#FFB74D",
            "error": "#E57373",
            "info": "#64B5F6",
        }


def get_status_color(status: TreatmentStatus) -> str:
    """Get color for treatment status"""
    colors = {
        TreatmentStatus.IN_PROGRESS: "#FFC107",
        TreatmentStatus.CURED: "#4CAF50",
        TreatmentStatus.TREATMENT_COMPLETED: "#2196F3",
        TreatmentStatus.NOT_CURED: "#F44336",
        TreatmentStatus.REFUSED: "#9E9E9E",
        TreatmentStatus.NO_CHANGE: "#9E9E9E",
    }
    return colors.get(status, "#9E9E9E")


def get_status_display(status: TreatmentStatus) -> str:
    """Get display text for treatment status"""
    lang = config.current_language
    
    if lang == Language.TAJIK:
        display = {
            TreatmentStatus.IN_PROGRESS: "🟡 Дар раванди табобат",
            TreatmentStatus.CURED: "🟢 Шифо шуд",
            TreatmentStatus.TREATMENT_COMPLETED: "🔵 Табобат ба анҷом расид",
            TreatmentStatus.NOT_CURED: "🔴 Шифо нашуд",
            TreatmentStatus.REFUSED: "⚪ Аз табобат саркашӣ кард",
            TreatmentStatus.NO_CHANGE: "⚪ Бе тағйирот",
        }
    else:  # Russian
        display = {
            TreatmentStatus.IN_PROGRESS: "🟡 В процессе лечения",
            TreatmentStatus.CURED: "🟢 Вылечен",
            TreatmentStatus.TREATMENT_COMPLETED: "🔵 Лечение завершено",
            TreatmentStatus.NOT_CURED: "🔴 Не удалось вылечить",
            TreatmentStatus.REFUSED: "⚪ Отказался от лечения",
            TreatmentStatus.NO_CHANGE: "⚪ Без изменений",
        }
    # Handle both enum and string inputs
    if isinstance(status, str):
        return status
    return display.get(status, str(status))


def get_translation(key: str) -> str:
    """Get translation for UI text based on current language"""
    lang = config.current_language
    
    translations = {
        Language.RUSSIAN: {
            "app_name": "Система управления лабораторией",
            "patients": "Пациенты",
            "statistics": "Статистика",
            "settings": "Настройки",
            "logout": "Выйти",
            "add_patient": "Добавить пациента",
            "edit_patient": "Редактировать",
            "delete_patient": "Удалить",
            "search": "Поиск",
            "export": "Экспорт",
            "import": "Импорт",
            "backup": "Резервная копия",
            "general_statistics": "Общая статистика",
            "treatment": "Лечение",
            "diseases": "Заболевания",
            "completed_treatment": "Завершено лечение",
            "avg_treatment_days": "Среднее время (дней)",
            "patients_by_doctor": "Пациенты по врачам",
            "disease_distribution": "Распределение по типам заболеваний",
            "status_distribution": "Распределение по статусам лечения",
            "total_patients": "Всего пациентов",
            "active_patients": "Активные пациенты",
            "completed_patients": "Завершенные",
            "language": "Язык",
        },
        Language.TAJIK: {
            "app_name": "Системаи идоракунии лаборатория",
            "patients": "Беморон",
            "statistics": "Омор",
            "settings": "Танзимот",
            "logout": "Баромадан",
            "add_patient": "Илова кардани бемор",
            "edit_patient": "Таҳрир кардан",
            "delete_patient": "Нест кардан",
            "search": "Ҷустуҷӯ",
            "export": "Содирот",
            "import": "Воридот",
            "backup": "Нусхаи захиравӣ",
            "general_statistics": "Омири умумӣ",
            "treatment": "Табобат",
            "diseases": "Бемориҳо",
            "completed_treatment": "Табобат ба анҷом расид",
            "avg_treatment_days": "Вақти миёна (рӯз)",
            "patients_by_doctor": "Беморон аз рӯи духтурон",
            "disease_distribution": "Тақсимот аз рӯи намудҳои беморӣ",
            "status_distribution": "Тақсимот аз рӯи вазъи табобат",
            "total_patients": "Ҳамаи беморон",
            "active_patients": "Беморони фаъол",
            "completed_patients": "Ба анҷом расида",
            "language": "Забон",
        }
    }
    
    return translations.get(lang, {}).get(key, key)
