"""
Statistics service for Laboratory Management System
Handles statistics and data analysis
"""
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from database import db_manager
from models import Patient, TreatmentStatus, ActionLog
from config import config


logger = logging.getLogger(__name__)


class StatisticsService:
    """Statistics service class"""
    
    @staticmethod
    def get_general_statistics() -> Dict:
        """Get general statistics about patients"""
        try:
            with db_manager.session_scope() as session:
                total_patients = session.query(Patient).count()
                
                # Patients by status
                status_stats = {}
                for status in TreatmentStatus:
                    count = session.query(Patient).filter(
                        Patient.treatment_status == status
                    ).count()
                    status_stats[status.value] = count
                
                # Patients by disease type
                disease_type_stats = session.query(
                    Patient.disease_type,
                    func.count(Patient.id)
                ).group_by(Patient.disease_type).all()
                
                # Patients by gender
                gender_stats = session.query(
                    Patient.gender,
                    func.count(Patient.id)
                ).group_by(Patient.gender).all()
                
                # Patients by birth year (last 10 years)
                current_year = datetime.now().year
                birth_year_stats = session.query(
                    Patient.birth_year,
                    func.count(Patient.id)
                ).filter(
                    Patient.birth_year >= current_year - 100
                ).group_by(Patient.birth_year).order_by(Patient.birth_year.desc()).all()
                
                # New patients this month
                this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                new_this_month = session.query(Patient).filter(
                    Patient.registration_date >= this_month
                ).count()
                
                # New patients this year
                this_year = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                new_this_year = session.query(Patient).filter(
                    Patient.registration_date >= this_year
                ).count()
                
                return {
                    'total_patients': total_patients,
                    'by_status': {s.value: status_stats.get(s.value, 0) for s in TreatmentStatus},
                    'by_disease_type': {dt: count for dt, count in disease_type_stats},
                    'by_gender': {str(g): count for g, count in gender_stats},
                    'by_birth_year': {str(by): count for by, count in birth_year_stats},
                    'new_this_month': new_this_month,
                    'new_this_year': new_this_year,
                }
                
        except Exception as e:
            logger.error(f"Error getting general statistics: {e}")
            return {}
    
    @staticmethod
    def get_monthly_statistics(year: int = None) -> Dict:
        """
        Get monthly statistics for a given year
        
        Args:
            year: Year to get statistics for (default: current year)
        """
        try:
            if year is None:
                year = datetime.now().year
            
            with db_manager.session_scope() as session:
                monthly_stats = {}
                
                for month in range(1, 13):
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1)
                    else:
                        end_date = datetime(year, month + 1, 1)
                    
                    count = session.query(Patient).filter(
                        and_(
                            Patient.registration_date >= start_date,
                            Patient.registration_date < end_date
                        )
                    ).count()
                    
                    monthly_stats[month] = count
                
                return monthly_stats
                
        except Exception as e:
            logger.error(f"Error getting monthly statistics: {e}")
            return {}
    
    @staticmethod
    def get_disease_statistics() -> Dict:
        """Get detailed disease statistics"""
        try:
            with db_manager.session_scope() as session:
                # Disease types with counts
                disease_types = session.query(
                    Patient.disease_type,
                    func.count(Patient.id)
                ).group_by(Patient.disease_type).all()
                
                # Disease names with counts
                disease_names = session.query(
                    Patient.disease_name,
                    func.count(Patient.id)
                ).group_by(Patient.disease_name).all()
                
                # Disease by status
                disease_by_status = session.query(
                    Patient.disease_type,
                    Patient.treatment_status,
                    func.count(Patient.id)
                ).group_by(Patient.disease_type, Patient.treatment_status).all()
                
                # Organize by status
                disease_by_status_dict = {}
                for disease_type, status, count in disease_by_status:
                    if disease_type not in disease_by_status_dict:
                        disease_by_status_dict[disease_type] = {}
                    disease_by_status_dict[disease_type][status.value] = count
                
                return {
                    'by_type': {dt: count for dt, count in disease_types},
                    'by_name': {dn: count for dn, count in disease_names},
                    'by_type_and_status': disease_by_status_dict,
                }
                
        except Exception as e:
            logger.error(f"Error getting disease statistics: {e}")
            return {}
    
    @staticmethod
    def get_treatment_statistics() -> Dict:
        """Get treatment outcome statistics"""
        try:
            with db_manager.session_scope() as session:
                # Treatment status distribution
                status_distribution = {}
                for status in TreatmentStatus:
                    count = session.query(Patient).filter(
                        Patient.treatment_status == status
                    ).count()
                    status_distribution[status.value] = count
                
                # Treatment by doctor
                treatment_by_doctor = session.query(
                    Patient.treating_doctor,
                    func.count(Patient.id)
                ).filter(
                    Patient.treating_doctor.isnot(None)
                ).group_by(Patient.treating_doctor).all()
                
                # Average treatment time (from registration to completion)
                # For completed treatments
                completed_patients = session.query(Patient).filter(
                    Patient.treatment_status.in_([
                        TreatmentStatus.CURED,
                        TreatmentStatus.TREATMENT_COMPLETED,
                        TreatmentStatus.NOT_CURED
                    ])
                ).all()
                
                # Detach patients from session
                for patient in completed_patients:
                    session.expunge(patient)
                
                treatment_times = []
                for patient in completed_patients:
                    if patient.updated_at and patient.registration_date:
                        days = (patient.updated_at - patient.registration_date).days
                        if days > 0:
                            treatment_times.append(days)
                
                avg_treatment_time = sum(treatment_times) / len(treatment_times) if treatment_times else 0
                
                return {
                    'status_distribution': status_distribution,
                    'by_doctor': {doc: count for doc, count in treatment_by_doctor},
                    'avg_treatment_days': avg_treatment_time,
                    'completed_count': len(completed_patients),
                }
                
        except Exception as e:
            logger.error(f"Error getting treatment statistics: {e}")
            return {}
    
    @staticmethod
    def get_activity_statistics(days: int = 30) -> Dict:
        """
        Get activity statistics for the last N days
        
        Args:
            days: Number of days to analyze
        """
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Actions by type
                actions_by_type = session.query(
                    ActionLog.action_type,
                    func.count(ActionLog.id)
                ).filter(
                    ActionLog.timestamp >= start_date
                ).group_by(ActionLog.action_type).all()
                
                # Daily activity
                daily_activity = {}
                for i in range(days):
                    day_start = (datetime.utcnow() - timedelta(days=i)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    day_end = day_start + timedelta(days=1)
                    
                    count = session.query(ActionLog).filter(
                        and_(
                            ActionLog.timestamp >= day_start,
                            ActionLog.timestamp < day_end
                        )
                    ).count()
                    
                    daily_activity[day_start.strftime('%Y-%m-%d')] = count
                
                # Most active users
                active_users = session.query(
                    ActionLog.user_id,
                    func.count(ActionLog.id)
                ).filter(
                    ActionLog.timestamp >= start_date
                ).group_by(ActionLog.user_id).order_by(
                    func.count(ActionLog.id).desc()
                ).limit(10).all()
                
                return {
                    'actions_by_type': {at: count for at, count in actions_by_type},
                    'daily_activity': dict(reversed(daily_activity.items())),
                    'active_users': {str(uid): count for uid, count in active_users},
                }
                
        except Exception as e:
            logger.error(f"Error getting activity statistics: {e}")
            return {}
    
    @staticmethod
    def get_upcoming_appointments(days: int = 7) -> List[Dict]:
        """
        Get upcoming appointments for the next N days
        
        Args:
            days: Number of days to look ahead
        """
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                future_date = datetime.utcnow() + timedelta(days=days)
                
                patients = session.query(Patient).filter(
                    and_(
                        Patient.next_appointment >= datetime.utcnow(),
                        Patient.next_appointment <= future_date
                    )
                ).order_by(Patient.next_appointment).all()
                
                # Detach patients from session
                for patient in patients:
                    session.expunge(patient)
                
                appointments = []
                for patient in patients:
                    appointments.append({
                        'patient_id': patient.id,
                        'full_name': patient.full_name,
                        'phone': patient.phone,
                        'appointment_date': patient.next_appointment,
                        'disease': patient.disease_name,
                        'doctor': patient.treating_doctor,
                    })
                
                return appointments
                
        except Exception as e:
            logger.error(f"Error getting upcoming appointments: {e}")
            return []


# Global statistics service instance
statistics_service = StatisticsService()
