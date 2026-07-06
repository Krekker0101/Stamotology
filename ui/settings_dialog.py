"""
Settings dialog UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config
from models import User, UserRole
from services.auth import auth_service
from database import db_manager


class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.init_ui()
        self.apply_theme()
        self.load_data()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Настройки")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Profile tab
        self.profile_tab = self.create_profile_tab()
        self.tab_widget.addTab(self.profile_tab, "Профиль")
        
        # Users tab (admin only)
        if self.user.role == UserRole.ADMIN:
            self.users_tab = self.create_users_tab()
            self.tab_widget.addTab(self.users_tab, "Пользователи")
        
        # Appearance tab
        self.appearance_tab = self.create_appearance_tab()
        self.tab_widget.addTab(self.appearance_tab, "Внешний вид")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.setMinimumHeight(40)
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_profile_tab(self) -> QWidget:
        """Create profile settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Username (read-only)
        username_layout = QHBoxLayout()
        username_label = QLabel("Имя пользователя:")
        username_label.setFixedWidth(150)
        self.username_edit = QLineEdit()
        self.username_edit.setReadOnly(True)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        
        # Full name
        name_layout = QHBoxLayout()
        name_label = QLabel("Полное имя:")
        name_label.setFixedWidth(150)
        self.full_name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.full_name_edit)
        layout.addLayout(name_layout)
        
        # Role (read-only)
        role_layout = QHBoxLayout()
        role_label = QLabel("Роль:")
        role_label.setFixedWidth(150)
        self.role_edit = QLineEdit()
        self.role_edit.setReadOnly(True)
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_edit)
        layout.addLayout(role_layout)
        
        # Change password section
        separator = QLabel("— Изменение пароля —")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)
        
        # Current password
        current_password_layout = QHBoxLayout()
        current_password_label = QLabel("Текущий пароль:")
        current_password_label.setFixedWidth(150)
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        current_password_layout.addWidget(current_password_label)
        current_password_layout.addWidget(self.current_password_edit)
        layout.addLayout(current_password_layout)
        
        # New password
        new_password_layout = QHBoxLayout()
        new_password_label = QLabel("Новый пароль:")
        new_password_label.setFixedWidth(150)
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        new_password_layout.addWidget(new_password_label)
        new_password_layout.addWidget(self.new_password_edit)
        layout.addLayout(new_password_layout)
        
        # Confirm password
        confirm_password_layout = QHBoxLayout()
        confirm_password_label = QLabel("Подтвердите пароль:")
        confirm_password_label.setFixedWidth(150)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_password_layout.addWidget(confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_edit)
        layout.addLayout(confirm_password_layout)
        
        # Change password button
        self.change_password_button = QPushButton("Изменить пароль")
        self.change_password_button.clicked.connect(self.change_password)
        layout.addWidget(self.change_password_button)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_users_tab(self) -> QWidget:
        """Create users management tab (admin only)"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add user button
        button_layout = QHBoxLayout()
        
        self.add_user_button = QPushButton("➕ Добавить пользователя")
        self.add_user_button.clicked.connect(self.add_user)
        button_layout.addWidget(self.add_user_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["Имя пользователя", "Полное имя", "Роль", "Действия"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.verticalHeader().setVisible(False)
        layout.addWidget(self.users_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Тема оформления:")
        theme_label.setFixedWidth(150)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая", config.Theme.LIGHT)
        self.theme_combo.addItem("Темная", config.Theme.DARK)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """Load current settings"""
        # Load profile data
        self.username_edit.setText(self.user.username)
        self.full_name_edit.setText(self.user.full_name)
        
        role_text = {
            UserRole.ADMIN: "Администратор",
            UserRole.DOCTOR: "Врач",
            UserRole.RECEPTIONIST: "Регистратор"
        }
        self.role_edit.setText(role_text.get(self.user.role, ""))
        
        # Load users if admin
        if self.user.role == UserRole.ADMIN:
            self.load_users()
    
    def load_users(self):
        """Load users table"""
        users = auth_service.get_all_users()
        
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # Username
            username_item = QTableWidgetItem(user.username)
            username_item.setData(Qt.ItemDataRole.UserRole, user.id)
            self.users_table.setItem(row, 0, username_item)
            
            # Full name
            self.users_table.setItem(row, 1, QTableWidgetItem(user.full_name))
            
            # Role
            role_text = {
                UserRole.ADMIN: "Администратор",
                UserRole.DOCTOR: "Врач",
                UserRole.RECEPTIONIST: "Регистратор"
            }
            self.users_table.setItem(row, 2, QTableWidgetItem(role_text.get(user.role, "")))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_button = QPushButton("Изменить роль")
            edit_button.setMaximumWidth(100)
            edit_button.clicked.connect(lambda checked, uid=user.id: self.edit_user_role(uid))
            actions_layout.addWidget(edit_button)
            
            reset_password_button = QPushButton("Сбросить пароль")
            reset_password_button.setMaximumWidth(110)
            reset_password_button.clicked.connect(lambda checked, uid=user.id, uname=user.username: self.reset_user_password(uid, uname))
            actions_layout.addWidget(reset_password_button)
            
            delete_button = QPushButton("Удалить")
            delete_button.setMaximumWidth(60)
            delete_button.clicked.connect(lambda checked, uid=user.id: self.delete_user(uid))
            actions_layout.addWidget(delete_button)
            
            actions_layout.addStretch()
            actions_widget.setLayout(actions_layout)
            self.users_table.setCellWidget(row, 3, actions_widget)
    
    def change_password(self):
        """Change user password"""
        current_password = self.current_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not current_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля пароля")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        
        if len(new_password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
            return
        
        success, message = auth_service.update_password(self.user.id, current_password, new_password)
        
        if success:
            QMessageBox.information(self, "Успех", message)
            self.current_password_edit.clear()
            self.new_password_edit.clear()
            self.confirm_password_edit.clear()
        else:
            QMessageBox.critical(self, "Ошибка", message)
    
    def add_user(self):
        """Add new user (admin only)"""
        from PySide6.QtWidgets import QDialogFormLayout, QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить пользователя")
        dialog.setFixedSize(400, 300)
        
        dialog_layout = QVBoxLayout()
        
        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Имя пользователя:"))
        username_edit = QLineEdit()
        username_layout.addWidget(username_edit)
        dialog_layout.addLayout(username_layout)
        
        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Пароль:"))
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_edit)
        dialog_layout.addLayout(password_layout)
        
        # Full name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Полное имя:"))
        name_edit = QLineEdit()
        name_layout.addWidget(name_edit)
        dialog_layout.addLayout(name_layout)
        
        # Role
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Роль:"))
        role_combo = QComboBox()
        role_combo.addItem("Регистратор", UserRole.RECEPTIONIST)
        role_combo.addItem("Врач", UserRole.DOCTOR)
        role_combo.addItem("Администратор", UserRole.ADMIN)
        role_layout.addWidget(role_combo)
        dialog_layout.addLayout(role_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Создать")
        cancel_button = QPushButton("Отмена")
        
        def create_user():
            username = username_edit.text().strip()
            password = password_edit.text()
            full_name = name_edit.text().strip()
            role = role_combo.currentData()
            
            if not all([username, password, full_name]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                return
            
            success, message = auth_service.create_user(username, password, full_name, role)
            if success:
                QMessageBox.information(dialog, "Успех", message)
                self.load_users()
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Ошибка", message)
        
        save_button.clicked.connect(create_user)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)
        
        dialog.setLayout(dialog_layout)
        dialog.exec()
    
    def edit_user_role(self, user_id: int):
        """Edit user role (admin only)"""
        if user_id == self.user.id:
            QMessageBox.warning(self, "Ошибка", "Нельзя изменить свою роль")
            return
        
        from PySide6.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Изменить роль пользователя")
        dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Выберите новую роль:"))
        
        role_combo = QComboBox()
        role_combo.addItem("Регистратор", UserRole.RECEPTIONIST)
        role_combo.addItem("Врач", UserRole.DOCTOR)
        role_combo.addItem("Администратор", UserRole.ADMIN)
        layout.addWidget(role_combo)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        
        def save_role():
            new_role = role_combo.currentData()
            success, message = auth_service.update_user(user_id, role=new_role)
            if success:
                self.load_users()
                QMessageBox.information(dialog, "Успех", message)
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Ошибка", message)
        
        save_button.clicked.connect(save_role)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def reset_user_password(self, user_id: int, username: str):
        """Reset user password (admin only)"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Сбросить пароль для пользователя '{username}'?\n\n"
            "Новый пароль будет: '123456'\n"
            "Пользователь должен будет изменить его при следующем входе.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = auth_service.reset_password(user_id, "123456")
            if success:
                QMessageBox.information(self, "Успех", message)
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def delete_user(self, user_id: int):
        """Delete user (admin only)"""
        if user_id == self.user.id:
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить текущего пользователя")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить этого пользователя?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = auth_service.delete_user(user_id)
            if success:
                self.load_users()
                QMessageBox.information(self, "Успех", message)
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def save_settings(self):
        """Save settings"""
        # Update full name
        full_name = self.full_name_edit.text().strip()
        if full_name:
            auth_service.update_user(self.user.id, full_name=full_name)
            self.user.full_name = full_name
        
        # Save theme preference
        selected_theme = self.theme_combo.currentData()
        # In a real app, this would be saved to database
        # For now, just close the dialog
        self.accept()
    
    def apply_theme(self):
        """Apply theme to the dialog"""
        colors = config.get_theme_colors(config.Theme.LIGHT)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
                background-color: transparent;
            }}
            QLineEdit, QComboBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                color: {colors['text']};
            }}
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QTableWidget {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                gridline-color: {colors['border']};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {colors['border']};
                color: {colors['text']};
                padding: 5px;
                border: none;
            }}
        """)
