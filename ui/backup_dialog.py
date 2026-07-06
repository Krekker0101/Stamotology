"""
Backup dialog UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from datetime import datetime
import config
from services.backup import backup_service
from utils.helpers import format_file_size


class BackupThread(QThread):
    """Thread for backup operations"""
    progress = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, operation: str, backup_path: str = None):
        super().__init__()
        self.operation = operation
        self.backup_path = backup_path
    
    def run(self):
        """Run backup operation"""
        if self.operation == "create":
            success, message, path = backup_service.create_backup()
            self.finished.emit(success, message)
        elif self.operation == "restore":
            success, message = backup_service.restore_backup(self.backup_path)
            self.finished.emit(success, message)


class BackupDialog(QDialog):
    """Dialog for backup and restore operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.apply_theme()
        self.load_backups()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Резервные копии")
        self.setFixedSize(700, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("💾 Управление резервными копиями")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.create_backup_button = QPushButton("➕ Создать резервную копию")
        self.create_backup_button.setMinimumHeight(40)
        self.create_backup_button.clicked.connect(self.create_backup)
        action_layout.addWidget(self.create_backup_button)
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # Backups table
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(4)
        self.backups_table.setHorizontalHeaderLabels([
            "Имя файла", "Размер", "Дата создания", "Действия"
        ])
        self.backups_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backups_table.verticalHeader().setVisible(False)
        self.backups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.backups_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.info_label)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.setMinimumHeight(40)
        self.close_button.clicked.connect(self.accept)
        close_layout.addWidget(self.close_button)
        
        layout.addLayout(close_layout)
        self.setLayout(layout)
    
    def load_backups(self):
        """Load backups list"""
        backups = backup_service.get_backup_list()
        
        self.backups_table.setRowCount(len(backups))
        
        for row, backup in enumerate(backups):
            # Filename
            name_item = QTableWidgetItem(backup['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, backup['path'])
            self.backups_table.setItem(row, 0, name_item)
            
            # Size
            size_item = QTableWidgetItem(format_file_size(backup['size']))
            self.backups_table.setItem(row, 1, size_item)
            
            # Date
            date_str = backup['created'].strftime("%d.%m.%Y %H:%M")
            self.backups_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            restore_button = QPushButton("Восстановить")
            restore_button.setMaximumWidth(100)
            restore_button.clicked.connect(lambda checked, path=backup['path']: self.restore_backup(path))
            actions_layout.addWidget(restore_button)
            
            delete_button = QPushButton("Удалить")
            delete_button.setMaximumWidth(80)
            delete_button.clicked.connect(lambda checked, path=backup['path']: self.delete_backup(path))
            actions_layout.addWidget(delete_button)
            
            actions_layout.addStretch()
            actions_widget.setLayout(actions_layout)
            self.backups_table.setCellWidget(row, 3, actions_widget)
        
        # Update info
        total_size = backup_service.get_backup_size()
        self.info_label.setText(f"Всего копий: {len(backups)} | Общий размер: {format_file_size(total_size)}")
    
    def create_backup(self):
        """Create a new backup"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Создать новую резервную копию?\n\nЭто может занять несколько секунд.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_processing(True)
            
            self.backup_thread = BackupThread("create")
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.start()
    
    def restore_backup(self, backup_path: str):
        """Restore from backup"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите восстановить базу данных из резервной копии?\n\n"
            "Текущие данные будут перезаписаны! Рекомендуется создать резервную копию перед восстановлением.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_processing(True)
            
            self.backup_thread = BackupThread("restore", backup_path)
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.start()
    
    def delete_backup(self, backup_path: str):
        """Delete a backup"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить эту резервную копию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = backup_service.delete_backup(backup_path)
            if success:
                self.load_backups()
                QMessageBox.information(self, "Успех", message)
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def on_backup_finished(self, success: bool, message: str):
        """Handle backup operation completion"""
        self.set_processing(False)
        
        if success:
            QMessageBox.information(self, "Успех", message)
            self.load_backups()
        else:
            QMessageBox.critical(self, "Ошибка", message)
    
    def set_processing(self, processing: bool):
        """Set processing state"""
        self.create_backup_button.setEnabled(not processing)
        self.backups_table.setEnabled(not processing)
        self.close_button.setEnabled(not processing)
        self.progress_bar.setVisible(processing)
        
        if processing:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
    
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
            QTableWidget {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                gridline-color: {colors['border']};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {colors['border']};
                color: {colors['text']};
                padding: 5px;
                border: none;
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
            QPushButton:disabled {{
                background-color: {colors['border']};
                color: {colors['text_secondary']};
            }}
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {colors['primary']};
            }}
        """)
