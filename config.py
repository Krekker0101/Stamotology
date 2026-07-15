"""
Configuration module for Laboratory Management System
"""
import os
import sys
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
    IN_PROGRESS = "в_процессе_лечения"
    CURED = "вылечен"
    TREATMENT_COMPLETED = "лечение_завершено"
    NOT_CURED = "не_удалось_вылечить"
    REFUSED = "отказался_от_лечения"
    NO_CHANGE = "без_изменений"


def get_base_path() -> Path:
    """Get the base path for the application (works for both dev and exe)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return Path(sys.executable).parent
    else:
        # Running in development
        return Path(__file__).parent


@dataclass
class AppConfig:
    """Application configuration"""
    
    # Base path
    BASE_PATH: Path = get_base_path()
    
    # Database
    DB_NAME: str = "laboratory.db"
    DATA_DIR: Path = None
    
    def __post_init__(self):
        """Initialize paths and create necessary directories"""
        if self.DATA_DIR is None:
            self.DATA_DIR = self.BASE_PATH / "data"
        
        self.DB_PATH = self.DATA_DIR / self.DB_NAME
        self.BACKUP_DIR = self.BASE_PATH / "backups"
        self.FILES_DIR = self.BASE_PATH / "files"
        self.LOG_FILE = self.BASE_PATH / "app.log"
        
        # Create necessary directories
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.FILES_DIR.mkdir(parents=True, exist_ok=True)
    
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
    BACKUP_DIR: Path = None
    MAX_BACKUPS: int = 10
    
    # Files
    FILES_DIR: Path = None
    
    # Theme
    DEFAULT_THEME: Theme = Theme.LIGHT
    
    # Language
    DEFAULT_LANGUAGE: Language = Language.RUSSIAN
    current_language: Language = Language.RUSSIAN
    
    # Default credentials (for first run)
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    
    # Logging
    LOG_FILE: Path = None
    LOG_LEVEL: str = "INFO"


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


def _normalize_status_value(status_str: str) -> str:
    normalized = str(status_str).strip().lower()
    if normalized.startswith('treatmentstatus.'):
        normalized = normalized.split('treatmentstatus.')[-1]
    return normalized.replace(' ', '').replace('-', '_')


def _coerce_status_enum(status) -> TreatmentStatus | None:
    if status is None:
        return None

    if isinstance(status, TreatmentStatus):
        return status

    if isinstance(status, str):
        normalized = _normalize_status_value(status)
        if normalized in {s.name.lower() for s in TreatmentStatus}:
            try:
                return TreatmentStatus[normalized.upper()]
            except KeyError:
                pass

        for enum_value in TreatmentStatus:
            if normalized == _normalize_status_value(enum_value.value):
                return enum_value

        normalized_no_underscore = normalized.replace('_', '')
        for enum_value in TreatmentStatus:
            if normalized_no_underscore == enum_value.name.lower().replace('_', ''):
                return enum_value
            if normalized_no_underscore == _normalize_status_value(enum_value.value).replace('_', ''):
                return enum_value

        return None

    if hasattr(status, 'name'):
        status_name = getattr(status, 'name', None)
        if isinstance(status_name, str):
            try:
                return TreatmentStatus[status_name]
            except KeyError:
                pass
        status_value = getattr(status, 'value', None)
        if isinstance(status_value, str):
            return _coerce_status_enum(status_value)

    return None


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

    status_enum = _coerce_status_enum(status)
    return colors.get(status_enum, "#9E9E9E")


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
            TreatmentStatus.IN_PROGRESS: "В процессе лечения",
            TreatmentStatus.CURED: "Вылечен",
            TreatmentStatus.TREATMENT_COMPLETED: "Лечение завершено",
            TreatmentStatus.NOT_CURED: "Не вылечен",
            TreatmentStatus.REFUSED: "Отказался от лечения",
            TreatmentStatus.NO_CHANGE: "Без изменений",
        }

    status_enum = _coerce_status_enum(status)
    if status_enum is None:
        return str(status)

    return display.get(status_enum, str(status))


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
            "treatment": "Статистика лечения",
            "treatment_statistics": "Статистика лечения",
            "diseases": "Заболевания",
            "completed_treatment": "Завершено лечение",
            "avg_treatment_days": "Среднее время (дней)",
            "patients_by_doctor": "Пациенты по врачам",
            "disease_distribution": "Распределение по типам заболеваний",
            "status_distribution": "Распределение по результатам",
            "result": "Результат",
            "total_patients": "Всего пациентов",
            "active_patients": "Активные пациенты",
            "completed_patients": "Завершенные",
            "new_this_month": "Новых за месяц",
            "new_this_year": "Новых за год",
            "activity": "Активность",
            "activity_last_30_days": "Активность за последние 30 дней",
            "month": "Месяц",
            "months": "Месяцы",
            "days": "Дни",
            "actions": "Действия",
            "quantity": "Количество",
            "doctors": "Врачи",
            "language": "Язык",
            "new_this_month": "Новых за месяц",
            "new_this_year": "Новых за год",
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
            "treatment": "Омори табобат",
            "treatment_statistics": "Омори табобат",
            "diseases": "Бемориҳо",
            "completed_treatment": "Табобат ба анҷом расид",
            "avg_treatment_days": "Вақти миёна (рӯз)",
            "patients_by_doctor": "Беморон аз рӯи духтурон",
            "disease_distribution": "Тақсимот аз рӯи намудҳои беморӣ",
            "status_distribution": "Тақсимот аз рӯи натиҷа",
            "result": "Натиҷа",
            "total_patients": "Ҳамаи беморон",
            "active_patients": "Беморони фаъол",
            "completed_patients": "Ба анҷом расида",
            "new_this_month": "Нови ин моҳ",
            "new_this_year": "Нови ин сол",
            "activity": "Фаъолият",
            "activity_last_30_days": "Фаъолият дар 30 рӯзи охир",
            "month": "Моҳ",
            "months": "Моҳҳо",
            "days": "Рӯзҳо",
            "actions": "Амалҳо",
            "quantity": "Миқдор",
            "doctors": "Духтурон",
            "language": "Забон",
            "new_this_month": "Нав дар моҳи ҷорӣ",
            "new_this_year": "Нав дар соли ҷорӣ",
        }
    }
    
    return translations.get(lang, {}).get(key, key)
