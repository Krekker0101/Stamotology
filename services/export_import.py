"""
Export/Import service for Laboratory Management System
Handles exporting data to Excel, PDF, CSV and importing from Excel, CSV
"""
import logging
from pathlib import Path
from typing import Tuple, List
import pandas as pd
from datetime import datetime
from database import db_manager
from models import Patient, TreatmentStatus, Gender
from config import config


logger = logging.getLogger(__name__)


class ExportImportService:
    """Export/Import service class"""
    
    @staticmethod
    def export_to_excel(output_path: str, filters: dict = None) -> Tuple[bool, str]:
        """
        Экспорт пациентов в Excel файл
        
        Args:
            output_path: Путь для сохранения Excel файла
            filters: Опциональные фильтры для применения
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                query = session.query(Patient)
                
                # Apply filters if provided
                if filters:
                    if 'status' in filters and filters['status']:
                        query = query.filter(Patient.treatment_status == filters['status'])
                    if 'disease_type' in filters and filters['disease_type']:
                        query = query.filter(Patient.disease_type == filters['disease_type'])
                
                patients = query.all()
                
                # Detach patients from session
                for patient in patients:
                    session.expunge(patient)
                
                # Convert to DataFrame
                data = []
                for patient in patients:
                    data.append({
                        'ID': patient.id,
                        'ФИО': patient.full_name,
                        'Телефон': patient.phone,
                        'Год рождения': patient.birth_year,
                        'Пол': 'Мужской' if patient.gender == Gender.MALE else 'Женский',
                        'Адрес': patient.address or '',
                        'Дата регистрации': patient.registration_date.strftime('%d.%m.%Y %H:%M'),
                        'Тип заболевания': patient.disease_type,
                        'Заболевание': patient.disease_name,
                        'Лечащий врач': patient.treating_doctor or '',
                        'Статус лечения': config.get_status_display(patient.treatment_status),
                        'Следующий прием': patient.next_appointment.strftime('%d.%m.%Y') if patient.next_appointment else '',
                        'Примечание': patient.notes or ''
                    })
                
                df = pd.DataFrame(data)
                
                # Save to Excel
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Пациенты')
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets['Пациенты']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                logger.info(f"Exported {len(patients)} patients to Excel: {output_path}")
                return True, f"Экспортировано {len(patients)} пациентов"
                
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False, f"Ошибка экспорта в Excel: {str(e)}"
    
    @staticmethod
    def export_to_csv(output_path: str, filters: dict = None) -> Tuple[bool, str]:
        """
        Экспорт пациентов в CSV файл
        
        Args:
            output_path: Путь для сохранения CSV файла
            filters: Опциональные фильтры для применения
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with db_manager.session_scope(expire_on_commit=False) as session:
                query = session.query(Patient)
                
                # Apply filters if provided
                if filters:
                    if 'status' in filters and filters['status']:
                        query = query.filter(Patient.treatment_status == filters['status'])
                    if 'disease_type' in filters and filters['disease_type']:
                        query = query.filter(Patient.disease_type == filters['disease_type'])
                
                patients = query.all()
                
                # Detach patients from session
                for patient in patients:
                    session.expunge(patient)
                
                # Convert to DataFrame
                data = []
                for patient in patients:
                    data.append({
                        'ID': patient.id,
                        'ФИО': patient.full_name,
                        'Телефон': patient.phone,
                        'Год рождения': patient.birth_year,
                        'Пол': 'Мужской' if patient.gender == Gender.MALE else 'Женский',
                        'Адрес': patient.address or '',
                        'Дата регистрации': patient.registration_date.strftime('%d.%m.%Y %H:%M'),
                        'Тип заболевания': patient.disease_type,
                        'Заболевание': patient.disease_name,
                        'Лечащий врач': patient.treating_doctor or '',
                        'Статус лечения': config.get_status_display(patient.treatment_status),
                        'Следующий прием': patient.next_appointment.strftime('%d.%m.%Y') if patient.next_appointment else '',
                        'Примечание': patient.notes or ''
                    })
                
                df = pd.DataFrame(data)
                
                # Save to CSV
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                logger.info(f"Exported {len(patients)} patients to CSV: {output_path}")
                return True, f"Экспортировано {len(patients)} пациентов"
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False, f"Ошибка экспорта в CSV: {str(e)}"
    
    @staticmethod
    def export_to_pdf(output_path: str, filters: dict = None) -> Tuple[bool, str]:
        """
        Экспорт пациентов в PDF файл
        
        Args:
            output_path: Путь для сохранения PDF файла
            filters: Опциональные фильтры для применения
            
        Returns:
            Tuple of (success, message)
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            with db_manager.session_scope(expire_on_commit=False) as session:
                query = session.query(Patient)
                
                # Apply filters if provided
                if filters:
                    if 'status' in filters and filters['status']:
                        query = query.filter(Patient.treatment_status == filters['status'])
                    if 'disease_type' in filters and filters['disease_type']:
                        query = query.filter(Patient.disease_type == filters['disease_type'])
                
                patients = query.all()
                
                # Detach patients from session
                for patient in patients:
                    session.expunge(patient)
                
                # Create PDF
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                doc = SimpleDocTemplate(str(output_file), pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title = Paragraph("Отчет по пациентам", styles['Title'])
                elements.append(title)
                elements.append(Spacer(1, 0.2 * inch))
                
                # Date
                date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
                date_para = Paragraph(f"Дата: {date_str}", styles['Normal'])
                elements.append(date_para)
                elements.append(Spacer(1, 0.2 * inch))
                
                # Table data
                table_data = [['ID', 'ФИО', 'Телефон', 'Год рождения', 'Заболевание', 'Статус']]
                
                for patient in patients:
                    table_data.append([
                        str(patient.id),
                        patient.full_name,
                        patient.phone,
                        str(patient.birth_year),
                        patient.disease_name,
                        config.get_status_display(patient.treatment_status)
                    ])
                
                # Create table
                table = Table(table_data, colWidths=[0.5*inch, 2*inch, 1*inch, 0.8*inch, 2*inch, 1.5*inch])
                
                # Style table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(table)
                
                # Build PDF
                doc.build(elements)
                
                logger.info(f"Exported {len(patients)} patients to PDF: {output_path}")
                return True, f"Экспортировано {len(patients)} пациентов"
                
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            return False, f"Ошибка экспорта в PDF: {str(e)}"
    
    @staticmethod
    def import_from_excel(input_path: str, user_id: int, update_existing: bool = False) -> Tuple[bool, str, int]:
        """
        Импорт пациентов из Excel файла
        
        Args:
            input_path: Путь к Excel файлу
            user_id: ID пользователя выполняющего импорт
            update_existing: Обновлять существующих пациентов или пропускать их
            
        Returns:
            Tuple of (success, message, imported_count)
        """
        try:
            input_file = Path(input_path)
            
            if not input_file.exists():
                return False, "Файл не найден", 0
            
            # Read Excel file
            df = pd.read_excel(input_file)
            
            # Required columns
            required_columns = ['ФИО', 'Телефон', 'Год рождения', 'Тип заболевания', 'Заболевание']
            
            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}", 0
            
            imported_count = 0
            errors = []
            
            with db_manager.session_scope() as session:
                for index, row in df.iterrows():
                    try:
                        # Map Excel columns to model fields
                        patient_data = {
                            'full_name': str(row['ФИО']).strip(),
                            'phone': str(row['Телефон']).strip(),
                            'birth_year': int(row['Год рождения']),
                            'gender': Gender.MALE if str(row.get('Пол', '')).strip() == 'Мужской' else Gender.FEMALE,
                            'address': str(row.get('Адрес', '')).strip() if pd.notna(row.get('Адрес')) else None,
                            'disease_type': str(row['Тип заболевания']).strip(),
                            'disease_name': str(row['Заболевание']).strip(),
                            'treating_doctor': str(row.get('Лечащий врач', '')).strip() if pd.notna(row.get('Лечащий врач')) else None,
                            'notes': str(row.get('Примечание', '')).strip() if pd.notna(row.get('Примечание')) else None,
                        }
                        
                        # Parse status if provided
                        status_str = str(row.get('Статус лечения', '')).strip() if pd.notna(row.get('Статус лечения')) else ''
                        if status_str:
                            for status in TreatmentStatus:
                                if status_str in config.get_status_display(status):
                                    patient_data['treatment_status'] = status
                                    break
                            else:
                                patient_data['treatment_status'] = TreatmentStatus.IN_PROGRESS
                        else:
                            patient_data['treatment_status'] = TreatmentStatus.IN_PROGRESS
                        
                        # Parse next appointment if provided
                        appointment_str = str(row.get('Следующий прием', '')).strip() if pd.notna(row.get('Следующий прием')) else ''
                        if appointment_str:
                            try:
                                patient_data['next_appointment'] = datetime.strptime(appointment_str, '%d.%m.%Y')
                            except:
                                pass
                        
                        # Check if patient already exists
                        existing = session.query(Patient).filter(
                            Patient.phone == patient_data['phone']
                        ).first()
                        
                        if existing:
                            if update_existing:
                                # Update existing patient
                                for field, value in patient_data.items():
                                    setattr(existing, field, value)
                                existing.updated_at = datetime.utcnow()
                                imported_count += 1
                            else:
                                # Skip existing patient
                                continue
                        else:
                            # Create new patient
                            patient_data['created_by'] = user_id
                            patient = Patient(**patient_data)
                            session.add(patient)
                            imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Строка {index + 1}: {str(e)}")
                        continue
                
                if errors:
                    logger.warning(f"Import completed with errors: {errors}")
                    return True, f"Импортировано {imported_count} пациентов. Ошибки: {len(errors)}", imported_count
                else:
                    logger.info(f"Imported {imported_count} patients from Excel")
                    return True, f"Успешно импортировано {imported_count} пациентов", imported_count
                
        except Exception as e:
            logger.error(f"Error importing from Excel: {e}")
            return False, f"Ошибка импорта из Excel: {str(e)}", 0
    
    @staticmethod
    def import_from_csv(input_path: str, user_id: int, update_existing: bool = False) -> Tuple[bool, str, int]:
        """
        Import patients from CSV file
        
        Args:
            input_path: Path to the CSV file
            user_id: ID of user performing the import
            update_existing: Whether to update existing patients or skip them
            
        Returns:
            Tuple of (success, message, imported_count)
        """
        try:
            input_file = Path(input_path)
            
            if not input_file.exists():
                return False, "Файл не найден", 0
            
            # Read CSV file
            df = pd.read_csv(input_path, encoding='utf-8-sig')
            
            # Required columns
            required_columns = ['ФИО', 'Телефон', 'Год рождения', 'Тип заболевания', 'Заболевание']
            
            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}", 0
            
            imported_count = 0
            errors = []
            
            with db_manager.session_scope() as session:
                for index, row in df.iterrows():
                    try:
                        # Map CSV columns to model fields
                        patient_data = {
                            'full_name': str(row['ФИО']).strip(),
                            'phone': str(row['Телефон']).strip(),
                            'birth_year': int(row['Год рождения']),
                            'gender': Gender.MALE if str(row.get('Пол', '')).strip() == 'Мужской' else Gender.FEMALE,
                            'address': str(row.get('Адрес', '')).strip() if pd.notna(row.get('Адрес')) else None,
                            'disease_type': str(row['Тип заболевания']).strip(),
                            'disease_name': str(row['Заболевание']).strip(),
                            'treating_doctor': str(row.get('Лечащий врач', '')).strip() if pd.notna(row.get('Лечащий врач')) else None,
                            'notes': str(row.get('Примечание', '')).strip() if pd.notna(row.get('Примечание')) else None,
                        }
                        
                        # Parse status if provided
                        status_str = str(row.get('Статус лечения', '')).strip() if pd.notna(row.get('Статус лечения')) else ''
                        if status_str:
                            for status in TreatmentStatus:
                                if status_str in config.get_status_display(status):
                                    patient_data['treatment_status'] = status
                                    break
                            else:
                                patient_data['treatment_status'] = TreatmentStatus.IN_PROGRESS
                        else:
                            patient_data['treatment_status'] = TreatmentStatus.IN_PROGRESS
                        
                        # Parse next appointment if provided
                        appointment_str = str(row.get('Следующий прием', '')).strip() if pd.notna(row.get('Следующий прием')) else ''
                        if appointment_str:
                            try:
                                patient_data['next_appointment'] = datetime.strptime(appointment_str, '%d.%m.%Y')
                            except:
                                pass
                        
                        # Check if patient already exists
                        existing = session.query(Patient).filter(
                            Patient.phone == patient_data['phone']
                        ).first()
                        
                        if existing:
                            if update_existing:
                                # Update existing patient
                                for field, value in patient_data.items():
                                    setattr(existing, field, value)
                                existing.updated_at = datetime.utcnow()
                                imported_count += 1
                            else:
                                # Skip existing patient
                                continue
                        else:
                            # Create new patient
                            patient_data['created_by'] = user_id
                            patient = Patient(**patient_data)
                            session.add(patient)
                            imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Строка {index + 1}: {str(e)}")
                        continue
                
                if errors:
                    logger.warning(f"Import completed with errors: {errors}")
                    return True, f"Импортировано {imported_count} пациентов. Ошибки: {len(errors)}", imported_count
                else:
                    logger.info(f"Imported {imported_count} patients from CSV")
                    return True, f"Успешно импортировано {imported_count} пациентов", imported_count
                
        except Exception as e:
            logger.error(f"Error importing from CSV: {e}")
            return False, f"Ошибка импорта из CSV: {str(e)}", 0


# Global export/import service instance
export_import_service = ExportImportService()
