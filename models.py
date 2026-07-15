"""
Database models for Laboratory Management System
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, 
    ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum


Base = declarative_base()


class UserRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    RECEPTIONIST = "receptionist"


class TreatmentStatus(enum.Enum):
    IN_PROGRESS = "в_процессе_лечения"
    CURED = "вылечен"
    TREATMENT_COMPLETED = "лечение_завершено"
    NOT_CURED = "не_удалось_вылечить"
    REFUSED = "отказался_от_лечения"
    NO_CHANGE = "без_изменений"


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.RECEPTIONIST)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    patients = relationship("Patient", back_populates="created_by_user")
    action_logs = relationship("ActionLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"


class Patient(Base):
    """Patient model"""
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    birth_year = Column(Integer, nullable=False, index=True)
    gender = Column(SQLEnum(Gender), nullable=False)
    address = Column(Text)
    registration_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    disease_type = Column(String(100), nullable=False, index=True)
    disease_name = Column(String(200), nullable=False, index=True)
    treating_doctor = Column(String(100))
    treatment_status = Column(SQLEnum(TreatmentStatus), 
                              default=TreatmentStatus.IN_PROGRESS, 
                              nullable=False, index=True)
    next_appointment = Column(DateTime, index=True)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by_user = relationship("User", back_populates="patients")
    attachments = relationship("Attachment", back_populates="patient", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="patient", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="patient", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_patient_full_name', 'full_name'),
        Index('idx_patient_phone', 'phone'),
        Index('idx_patient_birth_year', 'birth_year'),
        Index('idx_patient_disease_type', 'disease_type'),
        Index('idx_patient_disease_name', 'disease_name'),
        Index('idx_patient_treatment_status', 'treatment_status'),
        Index('idx_patient_registration_date', 'registration_date'),
    )
    
    def __repr__(self):
        return f"<Patient(id={self.id}, full_name='{self.full_name}', phone='{self.phone}')>"


class Attachment(Base):
    """File attachments for patients"""
    __tablename__ = 'attachments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    patient = relationship("Patient", back_populates="attachments")
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, file_name='{self.file_name}', patient_id={self.patient_id})>"


class ActionLog(Base):
    """Action log for tracking changes"""
    __tablename__ = 'action_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="action_logs")
    user = relationship("User", back_populates="action_logs")
    
    # Index for performance
    __table_args__ = (
        Index('idx_action_log_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ActionLog(id={self.id}, action_type='{self.action_type}', timestamp={self.timestamp})>"


class Reminder(Base):
    """Reminders for follow-up appointments"""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    reminder_date = Column(DateTime, nullable=False, index=True)
    reminder_text = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="reminders")
    
    # Index for performance
    __table_args__ = (
        Index('idx_reminder_date', 'reminder_date'),
    )
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, patient_id={self.patient_id}, reminder_date={self.reminder_date})>"


class Settings(Base):
    """Application settings"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Settings(key='{self.key}', value='{self.value}')>"
