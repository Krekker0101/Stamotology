"""
Patient dialog UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QDateEdit, QTextEdit, QPushButton, QMessageBox,
    QTabWidget, QWidget, QListWidget, QListWidgetItem, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from datetime import datetime
import config
from config import get_status_display
from models import Patient, TreatmentStatus, Gender, UserRole
from services.auth import auth_service
from services.patient import patient_service
from utils.helpers import get_unique_disease_types
from i18n import tr


class PatientDialog(QDialog):
    """Dialog for adding/editing patient information"""
    
    def __init__(self, user, patient: Patient = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.patient = patient
        self.is_edit = patient is not None
        self.init_ui()
        self.apply_theme()
        
        if self.is_edit:
            self.load_patient_data()
    
    def init_ui(self):
        """Initialize the UI"""
        title = tr("edit_patient_title") if self.is_edit else tr("add_patient_title")
        self.setWindowTitle(title)
        self.setFixedSize(700, 750)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Main info tab
        self.main_tab = self.create_main_tab()
        self.tab_widget.addTab(self.main_tab, tr("main_info"))
        
        # Attachments tab
        self.attachments_tab = self.create_attachments_tab()
        self.tab_widget.addTab(self.attachments_tab, tr("files"))
        
        # Reminders tab
        self.reminders_tab = self.create_reminders_tab()
        self.tab_widget.addTab(self.reminders_tab, tr("reminders"))
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton(tr("save_patient"))
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_patient)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton(tr("cancel"))
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_main_tab(self) -> QWidget:
        """Create main information tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # ID (read-only for edit)
        id_layout = QHBoxLayout()
        self.id_label = QLabel(tr("id") + ":")
        id_label = self.id_label
        id_label.setFixedWidth(140)
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        self.id_edit.setVisible(False)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_edit)
        layout.addLayout(id_layout)
        
        # Full name
        name_layout = QHBoxLayout()
        self.name_label = QLabel(tr("full_name_required"))
        name_label = self.name_label
        name_label.setFixedWidth(140)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("enter_full_name"))
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Phone
        phone_layout = QHBoxLayout()
        self.phone_label = QLabel(tr("phone_required"))
        phone_label = self.phone_label
        phone_label.setFixedWidth(140)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText(tr("enter_phone"))
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_edit)
        layout.addLayout(phone_layout)
        
        # Birth year and gender
        birth_gender_layout = QHBoxLayout()
        
        self.birth_label = QLabel(tr("birth_year_required"))
        birth_label = self.birth_label
        birth_label.setFixedWidth(140)
        self.birth_year_edit = QLineEdit()
        self.birth_year_edit.setPlaceholderText(tr("year"))
        self.birth_year_edit.setMaximumWidth(100)
        birth_gender_layout.addWidget(birth_label)
        birth_gender_layout.addWidget(self.birth_year_edit)
        
        self.gender_label = QLabel(tr("gender_required"))
        gender_label = self.gender_label
        self.gender_combo = QComboBox()
        self.gender_combo.addItems([tr("male"), tr("female")])
        birth_gender_layout.addWidget(gender_label)
        birth_gender_layout.addWidget(self.gender_combo)
        
        layout.addLayout(birth_gender_layout)
        
        # Address
        address_layout = QHBoxLayout()
        self.address_label = QLabel(tr("address"))
        address_label = self.address_label
        address_label.setFixedWidth(140)
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText(tr("enter_address"))
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_edit)
        layout.addLayout(address_layout)
        
        # Disease type and name
        disease_layout = QHBoxLayout()
        
        self.disease_type_label = QLabel(tr("disease_type_required"))
        disease_type_label = self.disease_type_label
        disease_type_label.setFixedWidth(140)
        self.disease_type_combo = QComboBox()
        self.disease_type_combo.setEditable(True)
        self.load_disease_types()
        disease_layout.addWidget(disease_type_label)
        disease_layout.addWidget(self.disease_type_combo)
        
        layout.addLayout(disease_layout)
        
        disease_name_layout = QHBoxLayout()
        self.disease_name_label = QLabel(tr("disease_name_required"))
        disease_name_label = self.disease_name_label
        disease_name_label.setFixedWidth(140)
        self.disease_name_edit = QLineEdit()
        self.disease_name_edit.setPlaceholderText(tr("enter_disease_name"))
        disease_name_layout.addWidget(disease_name_label)
        disease_name_layout.addWidget(self.disease_name_edit)
        layout.addLayout(disease_name_layout)
        
        # Treating doctor
        doctor_layout = QHBoxLayout()
        self.doctor_label = QLabel(tr("treating_doctor"))
        doctor_label = self.doctor_label
        doctor_label.setFixedWidth(140)
        self.doctor_combo = QComboBox()
        self.doctor_combo.setEditable(False)
        self.load_doctors()
        doctor_layout.addWidget(doctor_label)
        doctor_layout.addWidget(self.doctor_combo)
        layout.addLayout(doctor_layout)
        
        # Treatment status
        status_layout = QHBoxLayout()
        self.status_label = QLabel(tr("result_required"))
        status_label = self.status_label
        status_label.setFixedWidth(140)
        self.status_combo = QComboBox()
        for status in TreatmentStatus:
            self.status_combo.addItem(get_status_display(status), status)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)
        
        # Registration date
        appointment_layout = QHBoxLayout()
        self.appointment_label = QLabel(tr("registration_date_label"))
        appointment_label = self.appointment_label
        appointment_label.setFixedWidth(140)
        self.appointment_edit = QDateEdit()
        self.appointment_edit.setCalendarPopup(True)
        self.appointment_edit.setDate(QDate.currentDate())
        appointment_layout.addWidget(appointment_label)
        appointment_layout.addWidget(self.appointment_edit)
        layout.addLayout(appointment_layout)
        
        # Notes
        self.notes_label = QLabel(tr("notes"))
        notes_label = self.notes_label
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(tr("additional_info"))
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_attachments_tab(self) -> QWidget:
        """Create attachments tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Attachments list
        self.attachments_list = QListWidget()
        layout.addWidget(self.attachments_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_file_button = QPushButton(tr("add_file"))
        add_file_button = self.add_file_button
        add_file_button.clicked.connect(self.add_file)
        button_layout.addWidget(add_file_button)
        
        self.remove_file_button = QPushButton(tr("remove_file"))
        remove_file_button = self.remove_file_button
        remove_file_button.clicked.connect(self.remove_file)
        button_layout.addWidget(remove_file_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_reminders_tab(self) -> QWidget:
        """Create reminders tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Reminders list
        self.reminders_list = QListWidget()
        layout.addWidget(self.reminders_list)
        
        # Add reminder
        reminder_layout = QHBoxLayout()
        
        self.reminder_date_edit = QDateEdit()
        self.reminder_date_edit.setCalendarPopup(True)
        self.reminder_date_edit.setDate(QDate.currentDate())
        reminder_layout.addWidget(self.reminder_date_edit)
        
        self.reminder_text_edit = QLineEdit()
        self.reminder_text_edit.setPlaceholderText(tr("reminder_text"))
        reminder_layout.addWidget(self.reminder_text_edit)
        
        self.add_reminder_button = QPushButton(tr("add_reminder"))
        add_reminder_button = self.add_reminder_button
        add_reminder_button.clicked.connect(self.add_reminder)
        reminder_layout.addWidget(add_reminder_button)
        
        layout.addLayout(reminder_layout)
        
        widget.setLayout(layout)
        return widget
    
    def load_disease_types(self):
        """Load unique disease types"""
        types = get_unique_disease_types()
        self.disease_type_combo.clear()
        self.disease_type_combo.addItems(types)
    
    def load_doctors(self):
        """Load doctors and admins from registered users, excluding the current registrator"""
        doctors = []
        for user in auth_service.get_all_users():
            if not user.full_name or not user.is_active:
                continue
            if user.id == getattr(self.user, 'id', None):
                continue
            if user.role in {UserRole.DOCTOR, UserRole.ADMIN}:
                doctors.append(user.full_name)

        doctors = sorted(set(doctors))

        if self.patient and self.patient.treating_doctor and self.patient.treating_doctor not in doctors:
            doctors.append(self.patient.treating_doctor)
            doctors = sorted(set(doctors))

        self.doctor_combo.clear()
        self.doctor_combo.addItems(doctors)

        if self.patient and self.patient.treating_doctor:
            self.doctor_combo.setCurrentText(self.patient.treating_doctor)
    
    def load_patient_data(self):
        """Load patient data for editing"""
        if not self.patient:
            return
        
        self.id_edit.setText(str(self.patient.id))
        self.id_edit.setVisible(True)
        
        self.name_edit.setText(self.patient.full_name)
        self.phone_edit.setText(self.patient.phone)
        self.birth_year_edit.setText(str(self.patient.birth_year))
        self.gender_combo.setCurrentIndex(
            0 if self.patient.gender == Gender.MALE else 1
        )
        self.address_edit.setText(self.patient.address or "")
        self.disease_type_combo.setCurrentText(self.patient.disease_type)
        self.disease_name_edit.setText(self.patient.disease_name)
        self.doctor_combo.setCurrentText(self.patient.treating_doctor or "")
        
        # Set status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.patient.treatment_status:
                self.status_combo.setCurrentIndex(i)
                break
        
        if self.patient.registration_date:
            self.appointment_edit.setDate(
                QDate.fromString(
                    self.patient.registration_date.strftime("%Y-%m-%d"),
                    Qt.DateFormat.ISODate
                )
            )
        
        self.notes_edit.setText(self.patient.notes or "")
        
        # Load attachments
        self.load_attachments()
        
        # Load reminders
        self.load_reminders()
    
    def load_attachments(self):
        """Load patient attachments"""
        self.attachments_list.clear()
        if not self.patient:
            return
        
        attachments = patient_service.get_attachments(self.patient.id)
        for attachment in attachments:
            item = QListWidgetItem(f"{attachment.file_name} ({attachment.file_type})")
            item.setData(Qt.ItemDataRole.UserRole, attachment)
            self.attachments_list.addItem(item)
    
    def load_reminders(self):
        """Load patient reminders"""
        self.reminders_list.clear()
        if not self.patient:
            return
        
        reminders = patient_service.get_reminders(self.patient.id)
        for reminder in reminders:
            status = "✓" if reminder.is_completed else "○"
            date_str = reminder.reminder_date.strftime("%d.%m.%Y")
            item = QListWidgetItem(f"{status} {date_str}: {reminder.reminder_text}")
            item.setData(Qt.ItemDataRole.UserRole, reminder)
            self.reminders_list.addItem(item)
    
    def add_file(self):
        """Add file attachment"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("select_file"), "", tr("all_files")
        )
        
        if file_path:
            from pathlib import Path
            import shutil
            
            file_path = Path(file_path)
            if self.patient:
                # Copy file to files directory
                dest_dir = config.config.FILES_DIR / str(self.patient.id)
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                dest_path = dest_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                
                success, message = patient_service.add_attachment(
                    self.patient.id,
                    file_path.name,
                    str(dest_path),
                    file_path.stat().st_size,
                    file_path.suffix,
                    self.user.id
                )
                
                if success:
                    self.load_attachments()
                    QMessageBox.information(self, tr("success"), message)
                else:
                    QMessageBox.critical(self, tr("error"), message)
    
    def remove_file(self):
        """Remove selected file"""
        current_item = self.attachments_list.currentItem()
        if not current_item:
            return
        
        attachment = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, tr("confirm_delete"),
            tr("confirm_delete_file").format(name=attachment.file_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = patient_service.delete_attachment(attachment.id, self.user.id)
            if success:
                self.load_attachments()
                QMessageBox.information(self, tr("success"), message)
            else:
                QMessageBox.critical(self, tr("error"), message)
    
    def add_reminder(self):
        """Add reminder"""
        if not self.patient:
            QMessageBox.warning(self, tr("warning"), tr("save_patient_first"))
            return
        
        reminder_date = self.reminder_date_edit.date().toPython()
        reminder_text = self.reminder_text_edit.text().strip()
        
        if not reminder_text:
            QMessageBox.warning(self, tr("warning"), tr("enter_reminder_text"))
            return
        
        success, message = patient_service.add_reminder(
            self.patient.id,
            datetime.combine(reminder_date, datetime.min.time()),
            reminder_text,
            self.user.id
        )
        
        if success:
            self.reminder_text_edit.clear()
            self.load_reminders()
            QMessageBox.information(self, tr("success"), message)
        else:
            QMessageBox.critical(self, tr("error"), message)
    
    def save_patient(self):
        """Save patient data"""
        # Validate required fields
        name = self.name_edit.text().strip()
        phone = self.phone_edit.text().strip()
        birth_year = self.birth_year_edit.text().strip()
        disease_type = self.disease_type_combo.currentText().strip()
        disease_name = self.disease_name_edit.text().strip()
        
        if not all([name, phone, birth_year, disease_type, disease_name]):
            QMessageBox.warning(self, tr("error"), tr("fill_required_fields"))
            return
        
        try:
            birth_year = int(birth_year)
        except ValueError:
            QMessageBox.warning(self, tr("error"), tr("invalid_birth_year"))
            return
        
        # Prepare data
        data = {
            'full_name': name,
            'phone': phone,
            'birth_year': birth_year,
            'gender': Gender.MALE if self.gender_combo.currentIndex() == 0 else Gender.FEMALE,
            'address': self.address_edit.text().strip() or None,
            'disease_type': disease_type,
            'disease_name': disease_name,
            'treating_doctor': self.doctor_combo.currentText().strip() or None,
            'treatment_status': self.status_combo.currentData(),
            'registration_date': self.appointment_edit.date().toPython() if self.appointment_edit.date().isValid() else None,
            'notes': self.notes_edit.toPlainText().strip() or None,
        }
        
        if self.is_edit:
            success, message = patient_service.update_patient(self.patient.id, data, self.user.id)
        else:
            success, patient, message = patient_service.create_patient(data, self.user.id)
            if success:
                self.patient = patient
        
        if success:
            QMessageBox.information(self, tr("success"), message)
            self.accept()
        else:
            QMessageBox.critical(self, tr("error"), message)
    
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
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                color: {colors['text']};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 1px solid {colors['primary']};
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
            QListWidget {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
            }}
            QListWidget::item {{
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
        """)
    
    def update_language(self):
        """Update UI language"""
        # Update window title
        self.setWindowTitle(tr("edit_patient_title") if self.is_edit else tr("add_patient_title"))
        
        # Update tab names
        self.tab_widget.setTabText(0, tr("main_info"))
        self.tab_widget.setTabText(1, tr("files"))
        self.tab_widget.setTabText(2, tr("reminders"))
        
        # Update field labels
        self.id_label.setText(tr("id") + ":")
        self.name_label.setText(tr("full_name_required"))
        self.phone_label.setText(tr("phone_required"))
        self.birth_label.setText(tr("birth_year_required"))
        self.gender_label.setText(tr("gender_required"))
        self.address_label.setText(tr("address"))
        self.disease_type_label.setText(tr("disease_type_required"))
        self.disease_name_label.setText(tr("disease_name_required"))
        self.doctor_label.setText(tr("treating_doctor"))
        self.status_label.setText(tr("result_required"))
        self.appointment_label.setText(tr("registration_date_label"))
        self.notes_label.setText(tr("notes"))

        # Update buttons
        self.save_button.setText(tr("save_patient"))
        self.cancel_button.setText(tr("cancel"))
        self.add_file_button.setText(tr("add_file"))
        self.remove_file_button.setText(tr("remove_file"))
        self.add_reminder_button.setText(tr("add_reminder"))
        
        # Reload translated combo options without changing selected values
        current_gender = self.gender_combo.currentIndex()
        self.gender_combo.clear()
        self.gender_combo.addItems([tr("male"), tr("female")])
        self.gender_combo.setCurrentIndex(current_gender)

        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        for status in TreatmentStatus:
            self.status_combo.addItem(get_status_display(status), status)
        if current_status is not None:
            for index in range(self.status_combo.count()):
                if self.status_combo.itemData(index) == current_status:
                    self.status_combo.setCurrentIndex(index)
                    break
        
        # Update placeholders
        self.name_edit.setPlaceholderText(tr("enter_full_name"))
        self.phone_edit.setPlaceholderText(tr("enter_phone"))
        self.birth_year_edit.setPlaceholderText(tr("year"))
        self.address_edit.setPlaceholderText(tr("enter_address"))
        self.disease_name_edit.setPlaceholderText(tr("enter_disease_name"))
        self.notes_edit.setPlaceholderText(tr("additional_info"))
        self.reminder_text_edit.setPlaceholderText(tr("reminder_text"))
