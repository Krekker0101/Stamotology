"""
Laboratory Management System Installer
Creates a GUI installer that allows users to select installation path,
creates necessary folders, and adds desktop shortcut.
"""
import sys
import os
import shutil
from pathlib import Path
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                                QProgressBar, QMessageBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # In development, use the script's directory
        base_path = Path(__file__).parent
    
    path = Path(base_path) / relative_path
    
    # If path doesn't exist, try alternative locations for PyInstaller temp folder
    if not path.exists():
        # Try without the relative path prefix (for files at root of temp folder)
        if relative_path.startswith('dist/'):
            alt_path = Path(base_path) / relative_path.replace('dist/', '')
            if alt_path.exists():
                return alt_path
        # Try looking in parent directories (for development)
        elif not path.exists():
            alt_path = Path(__file__).parent.parent / relative_path
            if alt_path.exists():
                return alt_path
    
    return path


class InstallThread(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, source_dir, install_dir):
        super().__init__()
        self.source_dir = Path(source_dir)
        self.install_dir = Path(install_dir)
    
    def run(self):
        try:
            self.progress.emit(10)
            self.status.emit("Создание папок...")
            
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.install_dir / "data").mkdir(exist_ok=True)
            (self.install_dir / "backups").mkdir(exist_ok=True)
            (self.install_dir / "files").mkdir(exist_ok=True)
            (self.install_dir / "img").mkdir(exist_ok=True)
            
            self.progress.emit(30)
            self.status.emit("Копирование файлов...")
            
            # Copy main exe - use get_resource_path to find it in PyInstaller temp folder
            exe_source = get_resource_path("LaboratoryManagement.exe")
            if exe_source.exists():
                shutil.copy2(exe_source, self.install_dir / "LaboratoryManagement.exe")
            else:
                raise FileNotFoundError(f"Не найден файл: {exe_source}")
            
            self.progress.emit(50)
            
            # Copy images - use get_resource_path to find them in PyInstaller temp folder
            img_source_dir = get_resource_path("img")
            if img_source_dir.exists():
                for img_file in img_source_dir.glob("*"):
                    if img_file.is_file():
                        shutil.copy2(img_file, self.install_dir / "img" / img_file.name)
            
            self.progress.emit(70)
            self.status.emit("Создание ярлыка...")
            
            # Create desktop shortcut
            self.create_shortcut()
            
            self.progress.emit(90)
            self.status.emit("Завершение установки...")
            
            self.progress.emit(100)
            self.finished.emit(True, "Установка успешно завершена!")
            
        except Exception as e:
            self.finished.emit(False, f"Ошибка установки: {str(e)}")
    
    def create_shortcut(self):
        """Create desktop shortcut with high-quality icon"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "Laboratory Management System.lnk")
            target = str(self.install_dir / "LaboratoryManagement.exe")
            wDir = str(self.install_dir)
            icon = str(self.install_dir / "img" / "logo.ico")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = wDir
            shortcut.Description = "Laboratory Management System"
            # Set icon with index 0 (first icon in the file)
            if Path(icon).exists():
                shortcut.IconLocation = f"{icon},0"
            shortcut.save()
            
        except Exception as e:
            print(f"Error creating shortcut: {e}")
            raise Exception(f"Не удалось создать ярлык на рабочем столе: {e}")


class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.source_dir = Path(__file__).parent
        # Default to Local AppData to avoid permission issues
        self.install_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / "Laboratory Management"
        self.install_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Установка Laboratory Management System")
        self.setMinimumSize(500, 400)
        icon_path = get_resource_path("img/logo.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Laboratory Management System")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel("Версия 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        layout.addSpacing(20)
        
        # Installation path
        path_label = QLabel("Путь установки:")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_edit = QLabel(str(self.install_dir))
        self.path_edit.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Default paths
        layout.addSpacing(10)
        
        default_path_label = QLabel("Или выберите стандартный путь:")
        layout.addWidget(default_path_label)
        
        self.path_group = QButtonGroup(self)
        
        prog_files_radio = QRadioButton("Program Files")
        prog_files_radio.toggled.connect(lambda: self.set_default_path("program_files"))
        self.path_group.addButton(prog_files_radio, 1)
        layout.addWidget(prog_files_radio)
        
        prog_files_x86_radio = QRadioButton("Program Files (x86)")
        prog_files_x86_radio.toggled.connect(lambda: self.set_default_path("program_files_x86"))
        self.path_group.addButton(prog_files_x86_radio, 2)
        layout.addWidget(prog_files_x86_radio)
        
        local_radio = QRadioButton("Local AppData")
        local_radio.setChecked(True)
        local_radio.toggled.connect(lambda: self.set_default_path("local"))
        self.path_group.addButton(local_radio, 3)
        layout.addWidget(local_radio)
        
        custom_radio = QRadioButton("Другой путь")
        custom_radio.toggled.connect(lambda: self.set_default_path("custom"))
        self.path_group.addButton(custom_radio, 4)
        layout.addWidget(custom_radio)
        
        layout.addSpacing(20)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Установить")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.clicked.connect(self.start_installation)
        button_layout.addWidget(self.install_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для установки")
        if path:
            self.install_dir = Path(path) / "Laboratory Management"
            self.path_edit.setText(str(self.install_dir))
            custom_radio = self.path_group.button(4)
            custom_radio.setChecked(True)
    
    def set_default_path(self, path_type):
        if path_type == "program_files":
            self.install_dir = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "Laboratory Management"
        elif path_type == "program_files_x86":
            self.install_dir = Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "Laboratory Management"
        elif path_type == "local":
            self.install_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / "Laboratory Management"
        elif path_type == "custom":
            # Don't change path, user will browse
            return
        
        self.path_edit.setText(str(self.install_dir))
    
    def start_installation(self):
        # Check if source exe exists - use get_resource_path to find it in PyInstaller temp folder
        exe_source = get_resource_path("LaboratoryManagement.exe")
        if not exe_source.exists():
            QMessageBox.critical(self, "Ошибка", f"Не найден файл для установки:\n{exe_source}\n\nУбедитесь, что установщик собран правильно.")
            return
        
        # Check if install directory exists
        if self.install_dir.exists():
            reply = QMessageBox.question(
                self, 
                "Папка существует", 
                f"Папка {self.install_dir} уже существует. Продолжить установку?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Disable buttons
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.status_label.setText("Подготовка к установке...")
        
        # Start installation thread
        self.install_thread = InstallThread(self.source_dir, self.install_dir)
        self.install_thread.progress.connect(self.progress_bar.setValue)
        self.install_thread.status.connect(self.status_label.setText)
        self.install_thread.finished.connect(self.installation_finished)
        self.install_thread.start()
    
    def installation_finished(self, success, message):
        self.install_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, 
                "Установка завершена", 
                f"{message}\n\nПриложение установлено в:\n{self.install_dir}\n\nЯрлык создан на рабочем столе."
            )
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", message)
            self.progress_bar.setVisible(False)
            self.status_label.setText("")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    icon_path = get_resource_path("img/logo.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = InstallerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
