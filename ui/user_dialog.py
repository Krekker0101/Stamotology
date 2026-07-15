"""
User management dialog for Laboratory Management System
Allows administrators to create and manage user accounts
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFormLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config
from models import UserRole
from services.auth import auth_service
import bcrypt


class UserDialog(QDialog):
    """Dialog for creating/editing users"""
    
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.init_ui()
        
        if user:
            self.load_user_data()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Управление пользователями")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Создание нового пользователя" if not self.user else "Редактирование пользователя")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите логин")
        form_layout.addRow("Логин:", self.username_input)
        
        # Full name
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Введите ФИО")
        form_layout.addRow("ФИО:", self.fullname_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        form_layout.addRow("Пароль:", self.password_input)
        
        # Confirm password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Подтвердите пароль")
        form_layout.addRow("Подтверждение пароля:", self.confirm_password_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItem("Врач", UserRole.DOCTOR)
        self.role_combo.addItem("Регистратор", UserRole.RECEPTIONIST)
        # Admin role only for editing existing admin users
        if self.user and self.user.role == UserRole.ADMIN:
            self.role_combo.addItem("Администратор", UserRole.ADMIN)
        form_layout.addRow("Роль:", self.role_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.setMinimumHeight(36)
        self.save_button.clicked.connect(self.save_user)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setMinimumHeight(36)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_user_data(self):
        """Load existing user data into form"""
        if self.user:
            self.username_input.setText(self.user.username)
            self.fullname_input.setText(self.user.full_name)
            self.username_input.setEnabled(False)  # Cannot change username
            
            # Set role
            for i in range(self.role_combo.count()):
                if self.role_combo.itemData(i) == self.user.role:
                    self.role_combo.setCurrentIndex(i)
                    break
            
            # Hide password fields for editing (password change not implemented)
            self.password_input.setVisible(False)
            self.confirm_password_input.setVisible(False)
            form_layout = self.layout().itemAt(1).layout()
            form_layout.labelForField(self.password_input).setVisible(False)
            form_layout.labelForField(self.confirm_password_input).setVisible(False)
    
    def validate_input(self):
        """Validate user input"""
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role = self.role_combo.currentData()
        
        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите логин")
            return False
        
        if not fullname:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО")
            return False
        
        if not self.user:  # New user requires password
            if not password:
                QMessageBox.warning(self, "Ошибка", "Введите пароль")
                return False
            
            if len(password) < 6:
                QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов")
                return False
            
            if password != confirm_password:
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                return False
        
        return True
    
    def save_user(self):
        """Save user data"""
        if not self.validate_input():
            return
        
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentData()
        
        try:
            if self.user:
                # Update existing user
                success, message = auth_service.update_user(
                    self.user.id,
                    {
                        'full_name': fullname,
                        'role': role
                    }
                )
                if success:
                    QMessageBox.information(self, "Успех", message)
                    self.accept()
                else:
                    QMessageBox.critical(self, "Ошибка", message)
            else:
                # Create new user
                success, message = auth_service.create_user(
                    username=username,
                    password=password,
                    full_name=fullname,
                    role=role
                )
                if success:
                    QMessageBox.information(self, "Успех", 
                                          f"Пользователь создан успешно!\n\n"
                                          f"Логин: {username}\n"
                                          f"Пароль: {password}\n"
                                          f"Роль: {role.value}")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Ошибка", message)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")


class UserManagementDialog(QDialog):
    """Dialog for managing all users"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Управление пользователями")
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Управление пользователями")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Users list (simplified - using labels for now)
        self.users_container = QFrame()
        self.users_layout = QVBoxLayout()
        self.users_layout.setSpacing(10)
        self.users_container.setLayout(self.users_layout)
        layout.addWidget(self.users_container)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.add_button = QPushButton("➕ Добавить пользователя")
        self.add_button.setMinimumHeight(40)
        self.add_button.clicked.connect(self.add_user)
        button_layout.addWidget(self.add_button)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.setMinimumHeight(40)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_users(self):
        """Load all users"""
        try:
            users = auth_service.get_all_users()
            
            # Clear existing
            while self.users_layout.count():
                item = self.users_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            
            if not users:
                no_users = QLabel("Нет пользователей")
                no_users.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_users.setStyleSheet("color: #6c757d; font-size: 14px;")
                self.users_layout.addWidget(no_users)
                return
            
            # Add user cards
            for user in users:
                user_card = self.create_user_card(user)
                self.users_layout.addWidget(user_card)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки пользователей: {str(e)}")
    
    def create_user_card(self, user):
        """Create a card for displaying user info"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                background-color: #f8f9fa;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout()
        
        # User info
        info_layout = QVBoxLayout()
        
        username_label = QLabel(f"👤 {user.username}")
        username_font = QFont()
        username_font.setPointSize(12)
        username_font.setBold(True)
        username_label.setFont(username_font)
        info_layout.addWidget(username_label)
        
        role_text = self.get_role_display(user.role)
        role_label = QLabel(f"🔑 {role_text}")
        role_label.setStyleSheet("color: #6c757d;")
        info_layout.addWidget(role_label)
        
        fullname_label = QLabel(f"📛 {user.full_name}")
        fullname_label.setStyleSheet("color: #6c757d;")
        info_layout.addWidget(fullname_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Actions
        if user.role != UserRole.ADMIN:
            edit_button = QPushButton("✏️ Редактировать")
            edit_button.clicked.connect(lambda: self.edit_user(user))
            layout.addWidget(edit_button)
            
            delete_button = QPushButton("🗑️ Удалить")
            delete_button.setStyleSheet("background-color: #dc3545; color: white;")
            delete_button.clicked.connect(lambda: self.delete_user(user))
            layout.addWidget(delete_button)
        
        card.setLayout(layout)
        return card
    
    def get_role_display(self, role):
        """Get display text for role"""
        role_map = {
            UserRole.ADMIN: "Администратор",
            UserRole.DOCTOR: "Врач",
            UserRole.RECEPTIONIST: "Регистратор"
        }
        return role_map.get(role, str(role))
    
    def add_user(self):
        """Add new user"""
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()
    
    def edit_user(self, user):
        """Edit existing user"""
        dialog = UserDialog(self, user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()
    
    def delete_user(self, user):
        """Delete user"""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить пользователя {user.username}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = auth_service.delete_user(user.id)
            if success:
                QMessageBox.information(self, "Успех", message)
                self.load_users()
            else:
                QMessageBox.critical(self, "Ошибка", message)
