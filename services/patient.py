"""
Patient service for Laboratory Management System
Handles all patient-related operations
"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import or_, and_, cast
from sqlalchemy import String
from database import db_manager
from models import Patient, TreatmentStatus, Gender, ActionLog, Attachment, Reminder
from config import config


logger = logging.getLogger(__name__)


class PatientService:
    """Patient service class"""
    
    @staticmethod
    def create_patient(data: dict, user_id: int) -> Tuple[bool, Optional[Patient], str]:
        """
        Create a new patient
        
        Args:
            data: Dictionary with patient data
            user_id: ID of user creating the patient
            
        Returns:
            Tuple of (success, patient, message)
        """
        try:
            with db_manager.session_scope() as session:
                patient = Patient(
                    full_name=data.get('full_name'),
                    phone=data.get('phone'),
                    birth_year=data.get('birth_year'),
                    gender=data.get('gender'),
                    address=data.get('address'),
                    disease_type=data.get('disease_type'),
                    disease_name=data.get('disease_name'),
                    treating_doctor=data.get('treating_doctor'),
                    treatment_status=data.get('treatment_status', TreatmentStatus.IN_PROGRESS),
                    registration_date=data.get('registration_date'),
                    notes=data.get('notes'),
                    created_by=user_id
                )
                
                session.add(patient)
                session.flush()  # Get the patient ID
                
                # Log action
                action_log = ActionLog(
                    patient_id=patient.id,
                    user_id=user_id,
                    action_type="CREATE",
                    description=f"Создан новый пациент: {patient.full_name}"
                )
                session.add(action_log)
                
                # Detach patient from session for use outside
                session.expunge(patient)
                
                logger.info(f"Patient {patient.full_name} created successfully")
                return True, patient, "Пациент создан успешно"
                
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            return False, None, f"Ошибка создания пациента: {str(e)}"
    
    @staticmethod
    def get_patient_by_id(patient_id: int) -> Optional[Patient]:
        """Получить пациента по ID"""
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                if patient:
                    session.expunge(patient)
                return patient
        except Exception as e:
            logger.error(f"Error getting patient: {e}")
            return None
    
    @staticmethod
    def get_patients_paginated(page: int = 1, page_size: int = None, 
                              sort_by: str = 'id', sort_order: str = 'asc') -> Tuple[List[Patient], int]:
        """
        Get patients with pagination
        
        Returns:
            Tuple of (patients, total_count)
        """
        try:
            page_size = page_size or config.config.PAGE_SIZE
            offset = (page - 1) * page_size
            
            with db_manager.session_scope(expire_on_commit=False) as session:
                query = session.query(Patient)
                
                allowed_sort_columns = {
                    'id': Patient.id,
                    'full_name': Patient.full_name,
                    'registration_date': Patient.registration_date,
                    'birth_year': Patient.birth_year,
                    'treatment_status': Patient.treatment_status,
                }

                # Apply sorting with an allow-list to avoid accidental unsafe attributes
                sort_column = allowed_sort_columns.get(sort_by, Patient.id)
                if sort_order == 'desc':
                    sort_column = sort_column.desc()
                else:
                    sort_column = sort_column.asc()
                
                query = query.order_by(sort_column)
                
                query = query.order_by(Patient.registration_date.desc(), Patient.id.desc())

                # Get total count
                total_count = query.count()
                
                # Get paginated results
                patients = query.offset(offset).limit(page_size).all()
                
                # Detach all patients from session
                for patient in patients:
                    session.expunge(patient)
                
                return patients, total_count
                
        except Exception as e:
            logger.error(f"Error getting patients: {e}")
            return [], 0
    
    @staticmethod
    def search_patients(search_term: str, filters: dict = None, 
                       page: int = 1, page_size: int = None) -> Tuple[List[Patient], int]:
        """
        Search patients with filters
        
        Args:
            search_term: Search term for name, phone, ID, disease
            filters: Dictionary with additional filters
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (patients, total_count)
        """
        try:
            page_size = page_size or config.config.PAGE_SIZE
            offset = (page - 1) * page_size
            
            with db_manager.session_scope(expire_on_commit=False) as session:
                query = session.query(Patient)
                
                # Apply search term
                if search_term:
                    search_pattern = f"%{search_term}%"
                    query = query.filter(
                        or_(
                            Patient.full_name.ilike(search_pattern),
                            Patient.phone.ilike(search_pattern),
                            Patient.disease_name.ilike(search_pattern),
                            Patient.disease_type.ilike(search_pattern),
                            # Cast ID to string for search
                            cast(Patient.id, String).ilike(search_pattern)
                        )
                    )
                
                # Apply filters
                if filters:
                    if 'status' in filters and filters['status']:
                        query = query.filter(Patient.treatment_status == filters['status'])
                    if 'disease_type' in filters and filters['disease_type']:
                        query = query.filter(Patient.disease_type == filters['disease_type'])
                    if 'birth_year' in filters and filters['birth_year']:
                        query = query.filter(Patient.birth_year == filters['birth_year'])
                    if 'gender' in filters and filters['gender']:
                        query = query.filter(Patient.gender == filters['gender'])
                
                # Get total count
                total_count = query.count()
                
                # Get paginated results
                patients = query.offset(offset).limit(page_size).all()
                
                # Detach all patients from session
                for patient in patients:
                    session.expunge(patient)
                
                return patients, total_count
                
        except Exception as e:
            logger.error(f"Error searching patients: {e}")
            return [], 0
    
    @staticmethod
    def update_patient(patient_id: int, data: dict, user_id: int) -> Tuple[bool, str]:
        """
        Обновить информацию о пациенте
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                
                if not patient:
                    return False, "Пациент не найден"
                
                # Update fields
                old_values = {}
                for field, value in data.items():
                    if hasattr(patient, field) and value is not None:
                        old_values[field] = getattr(patient, field)
                        setattr(patient, field, value)
                
                patient.updated_at = datetime.utcnow()
                
                # Log action
                changes = []
                for field, old_value in old_values.items():
                    if old_value != data[field]:
                        changes.append(f"{field}: {old_value} -> {data[field]}")
                
                if changes:
                    action_log = ActionLog(
                        patient_id=patient.id,
                        user_id=user_id,
                        action_type="UPDATE",
                        description=f"Обновлен пациент {patient.full_name}: {', '.join(changes)}"
                    )
                    session.add(action_log)
                
                logger.info(f"Patient {patient.full_name} updated successfully")
                return True, "Пациент обновлен успешно"
                
        except Exception as e:
            logger.error(f"Error updating patient: {e}")
            return False, f"Ошибка обновления пациента: {str(e)}"
    
    @staticmethod
    def delete_patient(patient_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Удалить пациента
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                
                if not patient:
                    return False, "Пациент не найден"
                
                patient_name = patient.full_name
                
                # Log action before deletion
                action_log = ActionLog(
                    patient_id=patient.id,
                    user_id=user_id,
                    action_type="DELETE",
                    description=f"Удален пациент: {patient_name}"
                )
                session.add(action_log)
                
                # Delete patient (cascade will handle attachments, logs, reminders)
                session.delete(patient)
                
                logger.info(f"Patient {patient_name} deleted successfully")
                return True, "Пациент удален успешно"
                
        except Exception as e:
            logger.error(f"Error deleting patient: {e}")
            return False, f"Ошибка удаления пациента: {str(e)}"
    
    @staticmethod
    def get_patient_count() -> int:
        """Get total patient count"""
        try:
            with db_manager.session_scope() as session:
                return session.query(Patient).count()
        except Exception as e:
            logger.error(f"Error getting patient count: {e}")
            return 0
    
    @staticmethod
    def add_attachment(patient_id: int, file_name: str, file_path: str, 
                      file_size: int, file_type: str, user_id: int) -> Tuple[bool, str]:
        """
        Add file attachment to patient
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                
                if not patient:
                    return False, "Пациент не найден"
                
                attachment = Attachment(
                    patient_id=patient_id,
                    file_name=file_name,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=file_type,
                    uploaded_by=user_id
                )
                
                session.add(attachment)
                
                # Log action
                action_log = ActionLog(
                    patient_id=patient_id,
                    user_id=user_id,
                    action_type="ATTACHMENT",
                    description=f"Добавлен файл: {file_name}"
                )
                session.add(action_log)
                
                logger.info(f"Attachment {file_name} added to patient {patient_id}")
                return True, "Файл добавлен успешно"
                
        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
            return False, f"Ошибка добавления файла: {str(e)}"
    
    @staticmethod
    def get_attachments(patient_id: int) -> List[Attachment]:
        """Get all attachments for a patient"""
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                attachments = session.query(Attachment).filter(
                    Attachment.patient_id == patient_id
                ).all()
                for attachment in attachments:
                    session.expunge(attachment)
                return attachments
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []
    
    @staticmethod
    def delete_attachment(attachment_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete an attachment
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                attachment = session.query(Attachment).filter(
                    Attachment.id == attachment_id
                ).first()
                
                if not attachment:
                    return False, "Файл не найден"
                
                patient_id = attachment.patient_id
                file_name = attachment.file_name
                
                # Log action
                action_log = ActionLog(
                    patient_id=patient_id,
                    user_id=user_id,
                    action_type="ATTACHMENT_DELETE",
                    description=f"Удален файл: {file_name}"
                )
                session.add(action_log)
                
                # Delete attachment
                session.delete(attachment)
                
                logger.info(f"Attachment {file_name} deleted")
                return True, "Файл удален успешно"
                
        except Exception as e:
            logger.error(f"Error deleting attachment: {e}")
            return False, f"Ошибка удаления файла: {str(e)}"
    
    @staticmethod
    def add_reminder(patient_id: int, reminder_date: datetime, 
                    reminder_text: str, user_id: int) -> Tuple[bool, str]:
        """
        Add a reminder for a patient
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                
                if not patient:
                    return False, "Пациент не найден"
                
                reminder = Reminder(
                    patient_id=patient_id,
                    reminder_date=reminder_date,
                    reminder_text=reminder_text
                )
                
                session.add(reminder)
                
                logger.info(f"Reminder added for patient {patient_id}")
                return True, "Напоминание добавлено успешно"
                
        except Exception as e:
            logger.error(f"Error adding reminder: {e}")
            return False, f"Ошибка добавления напоминания: {str(e)}"
    
    @staticmethod
    def get_reminders(patient_id: int) -> List[Reminder]:
        """Get all reminders for a patient"""
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                reminders = session.query(Reminder).filter(
                    Reminder.patient_id == patient_id
                ).order_by(Reminder.reminder_date).all()
                for reminder in reminders:
                    session.expunge(reminder)
                return reminders
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    @staticmethod
    def get_upcoming_reminders(days: int = 7) -> List[Reminder]:
        """Get upcoming reminders for the next N days"""
        try:
            from datetime import timedelta
            with db_manager.session_scope(expire_on_commit=False) as session:
                future_date = datetime.utcnow() + timedelta(days=days)
                reminders = session.query(Reminder).filter(
                    and_(
                        Reminder.reminder_date >= datetime.utcnow(),
                        Reminder.reminder_date <= future_date,
                        Reminder.is_completed == False
                    )
                ).order_by(Reminder.reminder_date).all()
                for reminder in reminders:
                    session.expunge(reminder)
                return reminders
        except Exception as e:
            logger.error(f"Error getting upcoming reminders: {e}")
            return []
    
    @staticmethod
    def complete_reminder(reminder_id: int) -> Tuple[bool, str]:
        """
        Mark a reminder as completed
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope() as session:
                reminder = session.query(Reminder).filter(
                    Reminder.id == reminder_id
                ).first()
                
                if not reminder:
                    return False, "Напоминание не найдено"
                
                reminder.is_completed = True
                reminder.completed_at = datetime.utcnow()
                
                logger.info(f"Reminder {reminder_id} marked as completed")
                return True, "Напоминание отмечено как выполненное"
                
        except Exception as e:
            logger.error(f"Error completing reminder: {e}")
            return False, f"Ошибка обновления напоминания: {str(e)}"
    
    @staticmethod
    def get_action_logs(patient_id: int = None, limit: int = 100) -> List[ActionLog]:
        """
        Get action logs
        
        Args:
            patient_id: Optional patient ID to filter logs
            limit: Maximum number of logs to return
            
        Returns:
            List of action logs
        """
        try:
            with db_manager.session_scope() as session:
                query = session.query(ActionLog)
                
                if patient_id:
                    query = query.filter(ActionLog.patient_id == patient_id)
                
                return query.order_by(ActionLog.timestamp.desc()).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Error getting action logs: {e}")
            return []
    
    @staticmethod
    def get_statistics() -> dict:
        """Get patient statistics"""
        try:
            with db_manager.session_scope() as session:
                total = session.query(Patient).count()
                
                status_counts = {}
                for status in TreatmentStatus:
                    count = session.query(Patient).filter(
                        Patient.treatment_status == status
                    ).count()
                    status_counts[status.value] = count
                
                disease_types = session.query(
                    Patient.disease_type,
                    func.count(Patient.id)
                ).group_by(Patient.disease_type).all()
                
                return {
                    'total': total,
                    'by_status': status_counts,
                    'by_disease_type': {dt: count for dt, count in disease_types}
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


# Import func for statistics
from sqlalchemy import func


# Global patient service instance
patient_service = PatientService()
