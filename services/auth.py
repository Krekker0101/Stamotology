"""
Authentication service for Laboratory Management System
Handles user authentication and authorization
"""
import bcrypt
import logging
from typing import Optional, Tuple
from datetime import datetime
from database import db_manager
from models import User, UserRole


logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user
        
        Returns:
            Tuple of (success, user, message)
        """
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                user = session.query(User).filter(
                    User.username == username,
                    User.is_active == True
                ).first()
                
                if not user:
                    return False, None, "Пользователь не найден или отключен"
                
                if not AuthService.verify_password(password, user.password_hash):
                    return False, None, "Неверный пароль"
                
                # Update last login
                user.last_login = datetime.utcnow()
                session.commit()
                
                # Detach from session to use outside
                session.expunge(user)
                
                logger.info(f"User {username} authenticated successfully")
                return True, user, "Успешная авторизация"
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, None, f"Ошибка авторизации: {str(e)}"
    
    @staticmethod
    def create_user(username: str, password: str, full_name: str, 
                   role: UserRole = UserRole.RECEPTIONIST) -> Tuple[bool, str]:
        """
        Create a new user
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                # Check if username already exists
                existing_user = session.query(User).filter(
                    User.username == username
                ).first()
                
                if existing_user:
                    return False, "Пользователь с таким именем уже существует"
                
                # Hash password
                password_hash = AuthService.hash_password(password)
                
                # Create user
                user = User(
                    username=username,
                    password_hash=password_hash,
                    role=role,
                    full_name=full_name,
                    is_active=True
                )
                
                session.add(user)
                logger.info(f"User {username} created successfully")
                return True, "Пользователь создан успешно"
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, f"Ошибка создания пользователя: {str(e)}"
    
    @staticmethod
    def update_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Update user password
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return False, "Пользователь не найден"
                
                # Verify old password
                if not AuthService.verify_password(old_password, user.password_hash):
                    return False, "Неверный старый пароль"
                
                # Update password
                user.password_hash = AuthService.hash_password(new_password)
                logger.info(f"Password updated for user {user.username}")
                return True, "Пароль обновлен успешно"
                
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False, f"Ошибка обновления пароля: {str(e)}"
    
    @staticmethod
    def reset_password(user_id: int, new_password: str = "123456") -> Tuple[bool, str]:
        """
        Reset user password (admin only - no old password required)
        
        Args:
            user_id: ID of user to reset password for
            new_password: New password (default: "123456")
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return False, "Пользователь не найден"
                
                # Update password without verification
                user.password_hash = AuthService.hash_password(new_password)
                logger.info(f"Password reset for user {user.username} by admin")
                return True, f"Пароль сброшен на '{new_password}'"
                
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False, f"Ошибка сброса пароля: {str(e)}"
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    @staticmethod
    def get_all_users() -> list:
        """Get all active users"""
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                users = session.query(User).filter(User.is_active == True).all()
                for user in users:
                    session.expunge(user)
                return users
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    @staticmethod
    def update_user(user_id: int, full_name: str = None, 
                   role: UserRole = None, is_active: bool = None) -> Tuple[bool, str]:
        """
        Update user information
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return False, "Пользователь не найден"
                
                if full_name is not None:
                    user.full_name = full_name
                if role is not None:
                    user.role = role
                if is_active is not None:
                    user.is_active = is_active
                
                logger.info(f"User {user.username} updated successfully")
                return True, "Пользователь обновлен успешно"
                
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False, f"Ошибка обновления пользователя: {str(e)}"
    
    @staticmethod
    def delete_user(user_id: int) -> Tuple[bool, str]:
        """
        Delete a user (soft delete - set is_active to False)
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return False, "Пользователь не найден"
                
                # Prevent deleting the last admin
                if user.role == UserRole.ADMIN:
                    admin_count = session.query(User).filter(
                        User.role == UserRole.ADMIN,
                        User.is_active == True
                    ).count()
                    
                    if admin_count <= 1:
                        return False, "Невозможно удалить последнего администратора"
                
                user.is_active = False
                logger.info(f"User {user.username} deactivated successfully")
                return True, "Пользователь деактивирован успешно"
                
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False, f"Ошибка удаления пользователя: {str(e)}"
    
    @staticmethod
    def check_permission(user: User, required_role: UserRole) -> bool:
        """
        Check if user has required role or higher
        
        Role hierarchy: ADMIN > DOCTOR > RECEPTIONIST
        """
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.DOCTOR: 2,
            UserRole.RECEPTIONIST: 1
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level


# Global auth service instance
auth_service = AuthService()
