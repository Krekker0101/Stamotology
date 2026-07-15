"""
Main window UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QStackedWidget, QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor, QKeySequence, QShortcut
from pathlib import Path
import sys
import config
from i18n import tr
from models import User, UserRole
from ui.patients_view import PatientsView
from ui.patient_dialog import PatientDialog
from ui.search_view import SearchView
from ui.settings_dialog import SettingsDialog
from ui.user_dialog import UserManagementDialog
from services.patient import patient_service


def get_resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.current_theme = config.config.DEFAULT_THEME
        self._brand_animations = []
        self.init_ui()
        self.configure_shortcuts()
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
        self.statistics_view = None
        self.statistics_placeholder = QWidget()
        
        # Add views to stacked widget
        self.content_area.addWidget(self.patients_view)
        self.content_area.addWidget(self.search_view)
        self.content_area.addWidget(self.statistics_placeholder)
        
        # Show patients view by default
        self.content_area.setCurrentWidget(self.patients_view)

    def ensure_statistics_view(self):
        """Create the statistics view only when it is first opened."""
        if self.statistics_view is None:
            from ui.statistics_view import StatisticsView

            self.statistics_view = StatisticsView()
            self.statistics_view.apply_theme(self.current_theme)
            self.content_area.removeWidget(self.statistics_placeholder)
            self.statistics_placeholder.deleteLater()
            self.statistics_placeholder = None
            self.content_area.insertWidget(2, self.statistics_view)
        return self.statistics_view

    def create_brand_header(self) -> QFrame:
        """Create the compact app brand area used in the sidebar."""
        header = QFrame()
        header.setObjectName("brandHeader")
        header.setFixedHeight(68)

        header_layout = QHBoxLayout(header)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(2, 6, 2, 8)

        icon_frame = QFrame()
        icon_frame.setObjectName("brandIconFrame")
        icon_frame.setFixedSize(52, 52)

        shadow = QGraphicsDropShadowEffect(icon_frame)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(33, 150, 243, 70))
        icon_frame.setGraphicsEffect(shadow)

        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(8, 8, 8, 8)

        logo_label = QLabel()
        logo_label.setObjectName("brandIcon")
        logo_label.setFixedSize(36, 36)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        svg_path = get_resource_path("img/logo.svg")
        icon_path = get_resource_path("img/logo.ico")
        png_path = get_resource_path("img/logo.png")
        if svg_path.exists():
            logo_label.setPixmap(QIcon(str(svg_path)).pixmap(QSize(36, 36)))
        else:
            pixmap = QIcon(str(icon_path)).pixmap(QSize(34, 34)) if icon_path.exists() else QPixmap()
            if pixmap.isNull() and png_path.exists():
                pixmap = QPixmap(str(png_path)).scaled(
                    34, 34,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            logo_label.setPixmap(pixmap)
        icon_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.configure_brand_animation(logo_label)

        branding_label = QLabel(config.config.APP_NAME)
        branding_label.setObjectName("brandTitle")
        branding_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        branding_label.setWordWrap(False)
        branding_label.setMinimumWidth(0)
        branding_font = QFont("Segoe UI", 15)
        branding_font.setBold(True)
        branding_label.setFont(branding_font)

        header_layout.addWidget(icon_frame)
        header_layout.addWidget(branding_label, 1)
        return header

    def configure_brand_animation(self, logo_label: QLabel):
        """Add a subtle, paint-only breathing animation to the brand icon."""
        opacity_effect = QGraphicsOpacityEffect(logo_label)
        opacity_effect.setOpacity(0.96)
        logo_label.setGraphicsEffect(opacity_effect)

        opacity_animation = QPropertyAnimation(opacity_effect, b"opacity", self)
        opacity_animation.setStartValue(0.92)
        opacity_animation.setEndValue(1.0)
        opacity_animation.setDuration(2200)
        opacity_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        opacity_animation.setLoopCount(-1)
        opacity_animation.start()
        self._brand_animations.append(opacity_animation)
    
    def create_sidebar(self) -> QFrame:
        """Create sidebar with navigation buttons"""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        layout.addWidget(self.create_brand_header())
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # User info
        display_name = self.current_user.full_name
        if display_name == "Administrator":
            display_name = tr("administrator")
        user_label = QLabel(f"👤 {display_name}")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_font = QFont()
        user_font.setPointSize(9)
        user_label.setFont(user_font)
        layout.addWidget(user_label)
        
        # Role badge
        role_text = {
            UserRole.ADMIN: tr("admin_role"),
            UserRole.DOCTOR: tr("doctor_role"),
            UserRole.RECEPTIONIST: tr("receptionist_role")
        }
        self.role_label = QLabel(role_text.get(self.current_user.role, ""))
        self.role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_font = QFont()
        role_font.setPointSize(9)
        self.role_label.setFont(role_font)
        layout.addWidget(self.role_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Navigation buttons
        self.btn_patients = self.create_sidebar_button(f"📋 {tr('patients')}")
        self.btn_patients.clicked.connect(lambda: self.show_view(0))
        layout.addWidget(self.btn_patients)
        
        self.btn_search = self.create_sidebar_button(f"🔍 {tr('search')}")
        self.btn_search.clicked.connect(lambda: self.show_view(1))
        layout.addWidget(self.btn_search)
        
        self.btn_statistics = self.create_sidebar_button(f"📊 {tr('statistics')}")
        self.btn_statistics.clicked.connect(lambda: self.show_view(2))
        layout.addWidget(self.btn_statistics)
        
        # User management button (admin only)
        if self.current_user.role == UserRole.ADMIN:
            self.btn_users = self.create_sidebar_button(f"👥 {tr('users')}")
            self.btn_users.clicked.connect(self.show_user_management)
            layout.addWidget(self.btn_users)
        
        # Add patient button
        self.btn_add_patient = self.create_sidebar_button(f"➕ {tr('add_patient')}")
        self.btn_add_patient.clicked.connect(self.add_patient)
        layout.addWidget(self.btn_add_patient)
        
        layout.addStretch()
        
        # Language switcher
        lang_text = "🌐 Русский" if config.config.current_language == config.Language.RUSSIAN else "🌐 Тоҷикӣ"
        self.btn_language = self.create_sidebar_button(lang_text)
        self.btn_language.clicked.connect(self.switch_language)
        layout.addWidget(self.btn_language)
        
        # Bottom buttons
        self.btn_settings = self.create_sidebar_button(f"⚙️ {tr('settings')}")
        self.btn_settings.clicked.connect(self.show_settings_dialog)
        layout.addWidget(self.btn_settings)
        
        self.btn_logout = self.create_sidebar_button(f"🚪 {tr('logout')}")
        self.btn_logout.clicked.connect(self.logout)
        layout.addWidget(self.btn_logout)
        
        sidebar.setLayout(layout)
        return sidebar
    
    def create_sidebar_button(self, text: str) -> QPushButton:
        """Create a styled sidebar button with accessible focus behavior."""
        button = QPushButton(text)
        button.setMinimumHeight(46)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        button.setFont(QFont("Segoe UI", 10))
        return button

    def configure_shortcuts(self):
        """Register high-value keyboard shortcuts for clinical workflows."""
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_patient)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.show_view(1))
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.show_view(0))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.show_view(1))
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self.show_view(2))
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.show_settings_dialog)
    
    def show_view(self, index: int):
        """Show a specific view"""
        if index == 2:
            self.ensure_statistics_view()

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
    
    def show_settings_dialog(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.current_user, parent=self)
        if dialog.exec():
            self.apply_theme()
    
    def show_user_management(self):
        """Show user management dialog (admin only)"""
        dialog = UserManagementDialog(parent=self)
        dialog.exec()
    
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
        self.patients_view.update_language()
        self.search_view.refresh_data()
        self.search_view.update_language()
        if self.statistics_view is not None:
            self.statistics_view.refresh_data()
            self.statistics_view.update_language()
    
    def update_ui_language(self):
        """Update UI elements with current language"""
        # Update sidebar buttons
        self.btn_patients.setText(f"📋 {tr('patients')}")
        self.btn_search.setText(f"🔍 {tr('search')}")
        self.btn_statistics.setText(f"📊 {tr('statistics')}")
        self.btn_add_patient.setText(f"➕ {tr('add_patient')}")
        self.btn_settings.setText(f"⚙️ {tr('settings')}")
        self.btn_logout.setText(f"🚪 {tr('logout')}")
        
        # Update role badge
        role_text = {
            UserRole.ADMIN: tr("admin_role"),
            UserRole.DOCTOR: tr("doctor_role"),
            UserRole.RECEPTIONIST: tr("receptionist_role")
        }
        self.role_label.setText(role_text.get(self.current_user.role, ""))
    
    def logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, 
            tr('logout'), 
            tr('logout_confirm'),
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
                background-color: {colors['background']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
                background-color: transparent;
            }}
            #brandHeader {{
                background-color: {colors.get('surface_alt', colors['surface'])};
                border-radius: 18px;
            }}
            #brandTitle {{
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }}
            #brandIconFrame {{
                background-color: {colors['surface']};
                border-radius: 16px;
            }}
            QPushButton {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: 1px solid transparent;
                border-radius: 11px;
                text-align: left;
                padding-left: 15px;
                padding-right: 15px;
                font-size: 13px;
                font-weight: 600;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('surface_alt', colors['border'])};
                border-color: {colors['border']};
            }}
            QPushButton:focus {{
                border: 2px solid {colors['primary']};
            }}
            QPushButton[active="true"] {{
                background-color: {colors['primary']};
                color: white;
                font-weight: bold;
            }}
            QPushButton[active="true"]:hover {{
                background-color: {colors['primary_hover']};
            }}
        """)
        
        # Apply theme to views
        self.patients_view.apply_theme(self.current_theme)
        self.search_view.apply_theme(self.current_theme)
        if self.statistics_view is not None:
            self.statistics_view.apply_theme(self.current_theme)
    
    def set_theme(self, theme: config.Theme):
        """Set the application theme"""
        self.current_theme = theme
        self.apply_theme()
