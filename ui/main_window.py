"""
Main window UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QStackedWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import config
from models import User, UserRole
from ui.patients_view import PatientsView
from ui.patient_dialog import PatientDialog
from ui.search_view import SearchView
from ui.statistics_view import StatisticsView
from ui.settings_dialog import SettingsDialog
from ui.backup_dialog import BackupDialog
from services.patient import patient_service


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.current_theme = config.config.DEFAULT_THEME
        self.init_ui()
        self.apply_theme()
        self.load_data()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(config.config.APP_NAME)
        self.resize(config.config.WINDOW_WIDTH, config.config.WINDOW_HEIGHT)
        self.setMinimumSize(config.config.MIN_WINDOW_WIDTH, config.config.MIN_WINDOW_HEIGHT)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)
        
        central_widget.setLayout(main_layout)
        
        # Create views
        self.patients_view = PatientsView(self.current_user)
        self.search_view = SearchView(self.current_user)
        self.statistics_view = StatisticsView()
        
        # Add views to stacked widget
        self.content_area.addWidget(self.patients_view)
        self.content_area.addWidget(self.search_view)
        self.content_area.addWidget(self.statistics_view)
        
        # Show patients view by default
        self.content_area.setCurrentWidget(self.patients_view)
    
    def create_sidebar(self) -> QFrame:
        """Create sidebar with navigation buttons"""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # App title
        title_label = QLabel("Лаборатория")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # User info
        user_label = QLabel(f"Пользователь: {self.current_user.full_name}")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_font = QFont()
        user_font.setPointSize(10)
        user_label.setFont(user_font)
        layout.addWidget(user_label)
        
        # Role badge
        role_text = {
            UserRole.ADMIN: "Администратор",
            UserRole.DOCTOR: "Врач",
            UserRole.RECEPTIONIST: "Регистратор"
        }
        role_label = QLabel(role_text.get(self.current_user.role, ""))
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_font = QFont()
        role_font.setPointSize(9)
        role_label.setFont(role_font)
        layout.addWidget(role_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Navigation buttons
        self.btn_patients = self.create_sidebar_button("📋 Пациенты")
        self.btn_patients.clicked.connect(lambda: self.show_view(0))
        layout.addWidget(self.btn_patients)
        
        self.btn_search = self.create_sidebar_button("🔍 Поиск")
        self.btn_search.clicked.connect(lambda: self.show_view(1))
        layout.addWidget(self.btn_search)
        
        self.btn_statistics = self.create_sidebar_button("📊 Статистика")
        self.btn_statistics.clicked.connect(lambda: self.show_view(2))
        layout.addWidget(self.btn_statistics)
        
        # Add patient button
        self.btn_add_patient = self.create_sidebar_button("➕ Добавить пациента")
        self.btn_add_patient.clicked.connect(self.add_patient)
        layout.addWidget(self.btn_add_patient)
        
        layout.addStretch()
        
        # Language switcher
        self.btn_language = self.create_sidebar_button("🌐 Русский")
        self.btn_language.clicked.connect(self.switch_language)
        layout.addWidget(self.btn_language)
        
        # Bottom buttons
        self.btn_backup = self.create_sidebar_button("💾 Резервные копии")
        self.btn_backup.clicked.connect(self.show_backup_dialog)
        layout.addWidget(self.btn_backup)
        
        self.btn_settings = self.create_sidebar_button("⚙️ Настройки")
        self.btn_settings.clicked.connect(self.show_settings_dialog)
        layout.addWidget(self.btn_settings)
        
        self.btn_logout = self.create_sidebar_button("🚪 Выход")
        self.btn_logout.clicked.connect(self.logout)
        layout.addWidget(self.btn_logout)
        
        sidebar.setLayout(layout)
        return sidebar
    
    def create_sidebar_button(self, text: str) -> QPushButton:
        """Create a styled sidebar button"""
        button = QPushButton(text)
        button.setMinimumHeight(45)
        button.setFont(QFont())
        return button
    
    def show_view(self, index: int):
        """Show a specific view"""
        self.content_area.setCurrentIndex(index)
        
        # Update button states
        buttons = [self.btn_patients, self.btn_search, self.btn_statistics]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setProperty("active", True)
            else:
                btn.setProperty("active", False)
        
        self.apply_theme()
        
        # Refresh data when switching views
        if index == 0:
            self.patients_view.refresh_data()
        elif index == 1:
            self.search_view.refresh_data()
        elif index == 2:
            self.statistics_view.refresh_data()
    
    def add_patient(self):
        """Open dialog to add a new patient"""
        dialog = PatientDialog(self.current_user, parent=self)
        if dialog.exec():
            self.patients_view.refresh_data()
    
    def show_backup_dialog(self):
        """Show backup dialog"""
        dialog = BackupDialog(parent=self)
        dialog.exec()
    
    def show_settings_dialog(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.current_user, parent=self)
        if dialog.exec():
            self.apply_theme()
    
    def switch_language(self):
        """Switch between Russian and Tajik"""
        if config.config.current_language == config.Language.RUSSIAN:
            config.config.current_language = config.Language.TAJIK
            self.btn_language.setText("🌐 Тоҷикӣ")
        else:
            config.config.current_language = config.Language.RUSSIAN
            self.btn_language.setText("🌐 Русский")
        
        # Update UI with new language
        self.update_ui_language()
        # Refresh views to update translations
        self.patients_view.refresh_data()
        self.statistics_view.refresh_data()
    
    def update_ui_language(self):
        """Update UI elements with current language"""
        # Update sidebar buttons
        self.btn_patients.setText(f"📋 {config.get_translation('patients')}")
        self.btn_search.setText(f"🔍 {config.get_translation('search')}")
        self.btn_statistics.setText(f"📊 {config.get_translation('statistics')}")
        self.btn_add_patient.setText(f"➕ {config.get_translation('add_patient')}")
        self.btn_backup.setText(f"💾 {config.get_translation('backup')}")
        self.btn_settings.setText(f"⚙️ {config.get_translation('settings')}")
        self.btn_logout.setText(f"🚪 {config.get_translation('logout')}")
    
    def logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, 
            config.get_translation('logout'), 
            "Вы уверены, что хотите выйти?" if config.config.current_language == config.Language.RUSSIAN else "Шумо мутмаъин ҳастед, ки мехоҳед бароед?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
    
    def load_data(self):
        """Load initial data"""
        self.patients_view.refresh_data()
    
    def apply_theme(self):
        """Apply theme to the window"""
        colors = config.get_theme_colors(self.current_theme)
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['background']};
            }}
            QFrame {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text']};
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: none;
                border-radius: 5px;
                text-align: left;
                padding-left: 15px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {colors['border']};
            }}
            QPushButton[active="true"] {{
                background-color: {colors['primary']};
                color: white;
            }}
            QPushButton[active="true"]:hover {{
                background-color: {colors['primary_hover']};
            }}
        """)
        
        # Apply theme to views
        self.patients_view.apply_theme(self.current_theme)
        self.search_view.apply_theme(self.current_theme)
        self.statistics_view.apply_theme(self.current_theme)
    
    def set_theme(self, theme: config.Theme):
        """Set the application theme"""
        self.current_theme = theme
        self.apply_theme()
