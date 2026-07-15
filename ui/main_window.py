"""
Main window UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QStackedWidget, QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QElapsedTimer, QTimer,
    QPointF
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QColor, QKeySequence, QShortcut, QPainter,
    QPainterPath, QLinearGradient, QRadialGradient, QMovie
)
from pathlib import Path
import sys
import math
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
    """Resolve bundled resources in both development and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base_path / relative_path


class AnimatedDentalIcon(QWidget):
    """Self-contained premium dentistry icon animation for the brand header."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("brandIconFrame")
        self.setFixedSize(52, 52)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._elapsed = QElapsedTimer()
        self._elapsed.start()

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def paintEvent(self, event):
        """Draw only the icon; no parent layout or title animation is involved."""
        del event
        t = self._elapsed.elapsed() / 1000.0

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scale = 1.0 + 0.01 * (1.0 + math.sin(t * math.tau / 7.6)) / 2.0
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(scale, scale)
        painter.translate(-self.width() / 2, -self.height() / 2)

        shadow_strength = 0.42 + 0.08 * math.sin(t * math.tau / 7.6 + 0.9)
        shadow = QRadialGradient(QPointF(26, 43), 24)
        shadow.setColorAt(0.0, QColor(37, 99, 235, int(50 * shadow_strength)))
        shadow.setColorAt(0.68, QColor(14, 165, 233, int(22 * shadow_strength)))
        shadow.setColorAt(1.0, QColor(37, 99, 235, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawEllipse(QRectF(5, 31, 42, 17))

        icon_rect = QRectF(4, 3, 44, 44)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(icon_rect, 15, 15)

        gradient_phase = (math.sin(t * math.tau / 9.2) + 1.0) / 2.0
        bg = QLinearGradient(
            QPointF(5 + 7 * gradient_phase, 4),
            QPointF(48 - 7 * gradient_phase, 47),
        )
        bg.setColorAt(0.0, QColor("#F8FDFF"))
        bg.setColorAt(0.46, QColor("#DDF1FF"))
        bg.setColorAt(1.0, QColor("#BCE0FF"))
        painter.setBrush(bg)
        painter.drawPath(bg_path)

        painter.save()
        painter.setClipPath(bg_path)

        for x, y, radius, period, phase in (
            (15, 33, 1.35, 11.0, 0.3),
            (39, 19, 1.05, 13.0, 2.1),
        ):
            drift = math.sin(t * math.tau / period + phase)
            particle = QRadialGradient(QPointF(x + drift * 1.0, y - drift * 1.4), radius * 3)
            particle.setColorAt(0.0, QColor(125, 211, 252, 72))
            particle.setColorAt(1.0, QColor(125, 211, 252, 0))
            painter.setBrush(particle)
            painter.drawEllipse(QPointF(x + drift * 1.0, y - drift * 1.4), radius, radius)

        highlight_x = -14 + ((t % 9.0) / 9.0) * 80
        highlight = QLinearGradient(QPointF(highlight_x - 18, 2), QPointF(highlight_x + 18, 48))
        highlight.setColorAt(0.0, QColor(255, 255, 255, 0))
        highlight.setColorAt(0.48, QColor(255, 255, 255, 44))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(highlight)
        painter.drawRoundedRect(QRectF(highlight_x - 10, -2, 15, 58), 7, 7)

        tooth_float = 2.4 * math.sin(t * math.tau / 4.8)
        glow_alpha = 46 + int(18 * (1 + math.sin(t * math.tau / 6.8 + 0.5)) / 2)
        tooth_glow = QRadialGradient(QPointF(26, 25 + tooth_float), 17)
        tooth_glow.setColorAt(0.0, QColor(255, 255, 255, glow_alpha))
        tooth_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(tooth_glow)
        painter.drawEllipse(QRectF(11, 10 + tooth_float, 30, 30))

        painter.translate(0, tooth_float)
        tooth_path = QPainterPath()
        tooth_path.moveTo(18.0, 15.2)
        tooth_path.cubicTo(20.1, 11.6, 23.7, 12.0, 26.0, 14.0)
        tooth_path.cubicTo(28.3, 12.0, 31.9, 11.6, 34.0, 15.2)
        tooth_path.cubicTo(36.6, 19.6, 34.6, 24.8, 33.3, 28.8)
        tooth_path.cubicTo(32.4, 31.6, 32.0, 37.2, 29.6, 37.2)
        tooth_path.cubicTo(28.2, 37.2, 28.0, 31.7, 26.0, 31.7)
        tooth_path.cubicTo(24.0, 31.7, 23.8, 37.2, 22.4, 37.2)
        tooth_path.cubicTo(20.0, 37.2, 19.6, 31.6, 18.7, 28.8)
        tooth_path.cubicTo(17.4, 24.8, 15.4, 19.6, 18.0, 15.2)
        painter.setBrush(QColor(255, 255, 255, 245))
        painter.setPen(QPen(QColor(184, 218, 245, 88), 0.8))
        painter.drawPath(tooth_path)

        enamel = QPainterPath()
        enamel.moveTo(20.7, 16.7)
        enamel.cubicTo(22.1, 15.2, 24.0, 15.2, 25.6, 16.7)
        enamel.cubicTo(23.9, 21.8, 23.6, 26.0, 23.7, 30.1)
        enamel.cubicTo(21.7, 29.4, 20.5, 26.3, 19.8, 23.8)
        enamel.cubicTo(19.0, 20.9, 19.0, 18.8, 20.7, 16.7)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(226, 244, 255, 122))
        painter.drawPath(enamel)
        painter.translate(0, -tooth_float)

        sparkle_phase = math.sin(t * math.tau / 2.7 + 1.3)
        sparkle_opacity = 0.65 + 0.35 * (sparkle_phase + 1.0) / 2.0
        sparkle_scale = 0.96 + 0.08 * (math.sin(t * math.tau / 3.1 + 0.4) + 1.0) / 2.0
        painter.save()
        painter.translate(36.5, 13.0)
        painter.scale(sparkle_scale, sparkle_scale)
        star = QPainterPath()
        star.moveTo(0, -4.4)
        star.lineTo(1.25, -1.25)
        star.lineTo(4.4, 0)
        star.lineTo(1.25, 1.25)
        star.lineTo(0, 4.4)
        star.lineTo(-1.25, 1.25)
        star.lineTo(-4.4, 0)
        star.lineTo(-1.25, -1.25)
        star.closeSubpath()
        painter.setBrush(QColor(56, 189, 248, int(255 * sparkle_opacity)))
        painter.drawPath(star)
        painter.restore()

        painter.restore()

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 158), 1))
        painter.drawPath(bg_path)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.current_theme = config.config.DEFAULT_THEME
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

        # Animated brand icon: continuously looping logo.gif that replaces the
        # static logo while preserving size, spacing and shadow.
        logo_label = QLabel()
        logo_label.setObjectName("brandIcon")
        logo_label.setFixedSize(36, 36)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")

        self._brand_movie = QMovie(str(get_resource_path("img/logo.gif")))
        self._brand_movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self._brand_movie.setScaledSize(QSize(36, 36))
        logo_label.setMovie(self._brand_movie)
        self._brand_movie.start()

        icon_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

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
