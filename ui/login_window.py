"""
Login window UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import config
from services.auth import auth_service
from models import User


class LoginWindow(QWidget):
    """Login window for user authentication"""
    
    login_successful = Signal(object)  # Signal emitted when login is successful, passes User object
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()
        self.apply_theme()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"{config.config.APP_NAME} - Вход")
        self.setFixedSize(400, 500)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QLabel(config.config.APP_NAME)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Система управления лабораторией")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        layout.addWidget(subtitle_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Username field
        username_label = QLabel("Имя пользователя:")
        username_label.setFont(QFont())
        layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Введите имя пользователя")
        self.username_edit.setMinimumHeight(40)
        layout.addWidget(self.username_edit)
        
        # Password field
        password_label = QLabel("Пароль:")
        password_label.setFont(QFont())
        layout.addWidget(password_label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(40)
        layout.addWidget(self.password_edit)
        
        # Login button
        self.login_button = QPushButton("Войти")
        self.login_button.setMinimumHeight(45)
        self.login_button.setFont(QFont())
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)
        
        # Info label
        info_label = QLabel(
            f"По умолчанию: admin / {config.config.DEFAULT_ADMIN_PASSWORD}\n"
            "Пожалуйста, измените пароль после первого входа"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #666;")
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        layout.addWidget(info_label)
        
        # Version label
        version_label = QLabel(f"Версия {config.config.APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #999;")
        version_font = QFont()
        version_font.setPointSize(8)
        version_label.setFont(version_font)
        layout.addWidget(version_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Set focus to username field
        self.username_edit.setFocus()
        
        # Connect return key to login
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def apply_theme(self):
        """Apply theme to the window"""
        colors = config.get_theme_colors(config.config.DEFAULT_THEME)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLineEdit {{
                background-color: {colors['surface']};
                border: 2px solid {colors['border']};
                border-radius: 5px;
                padding: 8px;
                color: {colors['text']};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['primary']};
            }}
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary']};
            }}
        """)
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль")
            return
        
        # Authenticate user
        success, user, message = auth_service.authenticate(username, password)
        
        if success:
            self.current_user = user
            self.login_successful.emit(user)
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка входа", message)
            self.password_edit.clear()
            self.password_edit.setFocus()
    
    def get_current_user(self) -> User:
        """Get the currently logged in user"""
        return self.current_user
