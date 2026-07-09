"""
Patients view UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config
from models import Patient, TreatmentStatus
from services.patient import patient_service
from services.export_import import export_import_service
from ui.patient_dialog import PatientDialog
from utils.helpers import format_date, get_unique_disease_types
from i18n import tr


class PatientsView(QWidget):
    """View for displaying patients table with pagination"""
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.current_page = 1
        self.total_pages = 1
        self.total_count = 0
        self.current_sort = 'id'
        self.current_sort_order = 'asc'
        self.patients = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with search and actions
        header_layout = QHBoxLayout()
        
        # Patient count label
        self.count_label = QLabel(tr("total_patients_count").format(count=0))
        count_font = QFont()
        count_font.setBold(True)
        self.count_label.setFont(count_font)
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        # Quick search
        search_label = QLabel(tr("search") + ":")
        header_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("quick_search_placeholder"))
        self.search_edit.setMaximumWidth(200)
        self.search_edit.textChanged.connect(self.handle_quick_search)
        header_layout.addWidget(self.search_edit)
        
        # Add patient button
        add_button = QPushButton(tr("add_patient"))
        add_button.clicked.connect(self.add_patient)
        header_layout.addWidget(add_button)
        
        # Export button
        export_button = QPushButton(tr("export"))
        export_button.clicked.connect(self.export_data)
        header_layout.addWidget(export_button)
        
        layout.addLayout(header_layout)
        
        # Filter bar
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel(tr("filter_by_status") + ":"))
        self.status_filter = QComboBox()
        self.status_filter.addItem(tr("all_statuses"), None)
        for status in TreatmentStatus:
            self.status_filter.addItem(config.get_status_display(status), status)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addWidget(QLabel(tr("disease_type") + ":"))
        self.disease_filter = QComboBox()
        self.disease_filter.addItem(tr("all_types"), None)
        self.load_disease_types()
        self.disease_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.disease_filter)
        
        filter_layout.addStretch()
        
        # Sort
        filter_layout.addWidget(QLabel(tr("sort") + ":"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "ID (по возрастанию)",
            "ID (по убыванию)",
            "ФИО (А-Я)",
            "ФИО (Я-А)",
            "Дата регистрации (новые)",
            "Дата регистрации (старые)",
            "Год рождения",
            "Статус"
        ])
        self.sort_combo.currentIndexChanged.connect(self.apply_sort)
        filter_layout.addWidget(self.sort_combo)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
           tr("hdr_id"), tr("hdr_full_name"), tr("hdr_phone"), tr("hdr_birth_year"),
           tr("hdr_disease_type"), tr("hdr_disease_name"), tr("hdr_status"), tr("hdr_registration_date")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_patient)
        layout.addWidget(self.table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        
        self.first_button = QPushButton("<<")
        self.first_button.clicked.connect(lambda: self.go_to_page(1))
        pagination_layout.addWidget(self.first_button)
        
        self.prev_button = QPushButton("<")
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)
        
        self.page_label = QLabel(tr("page_label").format(current=1, total=1))
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pagination_layout.addWidget(self.page_label)
        
        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        self.last_button = QPushButton(">>")
        self.last_button.clicked.connect(lambda: self.go_to_page(self.total_pages))
        pagination_layout.addWidget(self.last_button)
        
        pagination_layout.addStretch()
        
        # Page size
        pagination_layout.addWidget(QLabel(tr("per_page")))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["25", "50", "100", "200"])
        self.page_size_combo.setCurrentText(str(config.config.PAGE_SIZE))
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        pagination_layout.addWidget(self.page_size_combo)
        
        layout.addLayout(pagination_layout)
        
        self.setLayout(layout)
    
    def load_disease_types(self):
        """Load disease types for filter"""
        types = get_unique_disease_types()
        self.disease_filter.clear()
        self.disease_filter.addItem("Все типы", None)
        for dtype in types:
            self.disease_filter.addItem(dtype, dtype)
    
    def refresh_data(self):
        """Refresh patient data"""
        self.load_data()
        self.load_disease_types()
    
    def load_data(self):
        """Load patients from database"""
        page_size = int(self.page_size_combo.currentText())
        
        # Apply filters
        filters = {}
        status_filter = self.status_filter.currentData()
        if status_filter:
            filters['status'] = status_filter
        
        disease_filter = self.disease_filter.currentData()
        if disease_filter:
            filters['disease_type'] = disease_filter
        
        # Apply search
        search_term = self.search_edit.text().strip()
        
        if search_term:
            self.patients, self.total_count = patient_service.search_patients(
                search_term, filters, self.current_page, page_size
            )
        else:
            self.patients, self.total_count = patient_service.get_patients_paginated(
                self.current_page, page_size, self.current_sort, self.current_sort_order
            )
        
        # Update total count
        self.total_pages = (self.total_count + page_size - 1) // page_size if self.total_count > 0 else 1
        self.count_label.setText(f"Всего пациентов: {self.total_count}")
        
        # Update table
        self.update_table()
        
        # Update pagination
        self.update_pagination()
    
    def update_table(self):
        """Update table with patient data"""
        self.table.setRowCount(len(self.patients))
        
        for row, patient in enumerate(self.patients):
            # ID
            id_item = QTableWidgetItem(str(patient.id))
            id_item.setData(Qt.ItemDataRole.UserRole, patient.id)
            self.table.setItem(row, 0, id_item)
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(patient.full_name))
            
            # Phone
            self.table.setItem(row, 2, QTableWidgetItem(patient.phone))
            
            # Birth year
            self.table.setItem(row, 3, QTableWidgetItem(str(patient.birth_year)))
            
            # Disease type
            self.table.setItem(row, 4, QTableWidgetItem(patient.disease_type))
            
            # Disease name
            self.table.setItem(row, 5, QTableWidgetItem(patient.disease_name))
            
            # Status
            status_item = QTableWidgetItem(config.get_status_display(patient.treatment_status))
            status_color = config.get_status_color(patient.treatment_status)
            status_item.setBackground(Qt.GlobalColor.transparent if status_color == "#9E9E9E" else Qt.GlobalColor.transparent)
            self.table.setItem(row, 6, status_item)
            
            # Registration date
            self.table.setItem(row, 7, QTableWidgetItem(format_date(patient.registration_date)))
    
    def update_pagination(self):
        """Update pagination controls"""
        self.page_label.setText(f"Страница {self.current_page} из {self.total_pages}")
        
        self.first_button.setEnabled(self.current_page > 1)
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
        self.last_button.setEnabled(self.current_page < self.total_pages)
    
    def handle_quick_search(self):
        """Handle quick search"""
        self.current_page = 1
        self.load_data()
    
    def apply_filters(self):
        """Apply filters"""
        self.current_page = 1
        self.load_data()
    
    def apply_sort(self):
        """Apply sorting"""
        sort_index = self.sort_combo.currentIndex()
        
        sort_mapping = {
            0: ('id', 'asc'),
            1: ('id', 'desc'),
            2: ('full_name', 'asc'),
            3: ('full_name', 'desc'),
            4: ('registration_date', 'desc'),
            5: ('registration_date', 'asc'),
            6: ('birth_year', 'asc'),
            7: ('treatment_status', 'asc'),
        }
        
        self.current_sort, self.current_sort_order = sort_mapping.get(sort_index, ('id', 'asc'))
        self.current_page = 1
        self.load_data()
    
    def change_page_size(self):
        """Change page size"""
        self.current_page = 1
        self.load_data()
    
    def go_to_page(self, page: int):
        """Go to specific page"""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.load_data()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
    
    def add_patient(self):
        """Add new patient"""
        dialog = PatientDialog(self.user, parent=self)
        if dialog.exec():
            self.load_data()
    
    def edit_patient(self):
        """Edit selected patient"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        item = self.table.item(current_row, 0)
        if not item:
            return
        
        patient_id = item.data(Qt.ItemDataRole.UserRole)
        if not patient_id:
            return
        
        patient = patient_service.get_patient_by_id(patient_id)
        
        if patient:
            dialog = PatientDialog(self.user, patient, parent=self)
            if dialog.exec():
                self.load_data()
    
    def delete_patient(self):
        """Delete selected patient"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите пациента для удаления")
            return
        
        patient_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        patient_name = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить пациента '{patient_name}'?\n\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = patient_service.delete_patient(patient_id, self.user.id)
            if success:
                self.load_data()
                QMessageBox.information(self, "Успех", message)
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def export_data(self):
        """Export patient data"""
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("Excel файлы (*.xlsx);;CSV файлы (*.csv);;PDF файлы (*.pdf)")
        
        if dialog.exec():
            file_path = dialog.selectedFiles()[0]
            file_ext = file_path.split('.')[-1].lower()
            
            # Apply current filters
            filters = {}
            status_filter = self.status_filter.currentData()
            if status_filter:
                filters['status'] = status_filter
            
            disease_filter = self.disease_filter.currentData()
            if disease_filter:
                filters['disease_type'] = disease_filter
            
            if file_ext == 'xlsx':
                success, message = export_import_service.export_to_excel(file_path, filters)
            elif file_ext == 'csv':
                success, message = export_import_service.export_to_csv(file_path, filters)
            elif file_ext == 'pdf':
                success, message = export_import_service.export_to_pdf(file_path, filters)
            else:
                QMessageBox.warning(self, "Ошибка", "Неподдерживаемый формат файла")
                return
            
            if success:
                QMessageBox.information(self, "Успех", message)
            else:
                QMessageBox.critical(self, "Ошибка", message)
    
    def apply_theme(self, theme):
        """Apply theme to the view"""
        colors = config.get_theme_colors(theme)
        
        self.setStyleSheet(f"""
            QWidget {{
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
                border-right: 1px solid {colors['background']};
                border-bottom: 1px solid {colors['background']};
            }}
            QLineEdit, QComboBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                color: {colors['text']};
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
        """)
