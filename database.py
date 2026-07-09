"""
Database module for Laboratory Management System
Handles database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging
from pathlib import Path
import config
from models import Base


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


class DatabaseManager:
    """Database manager class"""
    
    def __init__(self, db_path=None):
        """Initialize database manager"""
        self.db_path = db_path or config.config.DB_PATH
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session"""
        try:
            # Create database directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create SQLite engine with optimizations
            db_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(
                db_url,
                echo=False,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                    "isolation_level": None
                },
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            # Create session factory
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
            )
            
            # Create tables
            self.create_tables()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables in the database"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self, expire_on_commit=True):
        """Provide a transactional scope around a series of operations"""
        session = self.SessionLocal()
        session.expire_on_commit = expire_on_commit
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connection closed")

    def switch_database(self, new_db_path):
        """Switch to another database file at runtime.

        Closes current connections, updates the config DB_PATH, and
        reinitializes the engine and session factory against the new file.
        """
        try:
            new_path = Path(new_db_path)
            # Close current connections
            self.close()
            # Update global config path
            import config as _config
            _config.config.DB_PATH = new_path
            # Update internal path and reinitialize
            self.db_path = new_path
            self._initialize_database()
            logger.info(f"Switched database to {new_path}")
        except Exception as e:
            logger.error(f"Failed to switch database: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


def get_db():
    """Get database session (dependency injection pattern)"""
    session = db_manager.get_session()
    try:
        return session
    finally:
        pass  # Session will be closed by caller


def init_db():
    """Initialize database with default data"""
    try:
        with db_manager.session_scope() as session:
            # Check if admin user exists
            from models import User, UserRole
            admin = session.query(User).filter(User.username == config.config.DEFAULT_ADMIN_USERNAME).first()
            
            if not admin:
                # Create default admin user
                import bcrypt
                password_hash = bcrypt.hashpw(
                    config.config.DEFAULT_ADMIN_PASSWORD.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                admin = User(
                    username=config.config.DEFAULT_ADMIN_USERNAME,
                    password_hash=password_hash,
                    role=UserRole.ADMIN,
                    full_name="Administrator",
                    is_active=True
                )
                session.add(admin)
                logger.info("Default admin user created")
            
            # Check if settings exist
            from models import Settings
            theme_setting = session.query(Settings).filter(Settings.key == "theme").first()
            if not theme_setting:
                theme_setting = Settings(key="theme", value=config.config.DEFAULT_THEME.value)
                session.add(theme_setting)
                logger.info("Default theme setting created")
        
        logger.info("Database initialized with default data")
        
    except Exception as e:
        logger.error(f"Failed to initialize database with default data: {e}")
        raise


if __name__ == "__main__":
    # Test database connection
    try:
        db_manager = DatabaseManager()
        init_db()
        print("Database initialized successfully!")
        db_manager.close()
    except Exception as e:
        print(f"Error: {e}")
