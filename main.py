"""
Main entry point for Laboratory Management System
"""
import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
import config
from database import db_manager, init_db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def get_resource_path(relative_path: str) -> Path:
    """Resolve bundled resources in both development and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base_path / relative_path


# Configure logging
logging.basicConfig(
    level=config.config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(config.config.APP_NAME)
    app.setApplicationVersion(config.config.APP_VERSION)
    
    # Set application icon
    icon_path = get_resource_path("img/logo.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # High DPI scaling is automatic in Qt 6, no need to set attributes
    # app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager._initialize_database()
        
        # Initialize default data
        logger.info("Initializing default data...")
        init_db()
        
        logger.info("Application started successfully")
        
        # Show login window
        login_window = LoginWindow()
        login_window.show()
        
        # Handle successful login
        def on_login_success(user):
            logger.info(f"User {user.username} logged in successfully")
            
            # Close login window
            login_window.close()
            
            # Show main window
            main_window = MainWindow(user)
            main_window.show()
        
        login_window.login_successful.connect(on_login_success)
        
        # Run application
        result = app.exec()
        
        # Close database connection
        db_manager.close()
        
        logger.info("Application closed")
        return result
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        
        from PySide6.QtWidgets import QMessageBox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Ошибка")
        msg_box.setText("Произошла критическая ошибка при запуске приложения.")
        msg_box.setDetailedText(str(e))
        msg_box.exec()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
