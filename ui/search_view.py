"""
Search view UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config
from config import get_status_display
from models import TreatmentStatus
from services.patient import patient_service
from ui.patient_dialog import PatientDialog
from utils.helpers import format_date, get_unique_disease_types
from i18n import tr


class SearchView(QWidget):
    """Advanced search view for patients"""
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.patients = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel(f"🔍 {tr('advanced_search')}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Search fields
        search_layout = QVBoxLayout()
        
        # Name/Phone/ID search
        general_layout = QHBoxLayout()
        general_layout.addWidget(QLabel(tr("name_phone_id")))
        self.general_search = QLineEdit()
        self.general_search.setPlaceholderText(tr("enter_search"))
        general_layout.addWidget(self.general_search)
        search_layout.addLayout(general_layout)
        
        # Disease search
        disease_layout = QHBoxLayout()
        disease_layout.addWidget(QLabel(tr("disease")))
        self.disease_search = QLineEdit()
        self.disease_search.setPlaceholderText(tr("disease_name_placeholder"))
        disease_layout.addWidget(self.disease_search)
        search_layout.addLayout(disease_layout)
        
        # Filters row
        filter_row = QHBoxLayout()
        
        filter_row.addWidget(QLabel(tr("status") + ":"))
        self.status_filter = QComboBox()
        self.status_filter.addItem(tr("all_statuses"), None)
        for status in TreatmentStatus:
            self.status_filter.addItem(get_status_display(status), status)
        filter_row.addWidget(self.status_filter)
        
        filter_row.addWidget(QLabel(tr("disease_type") + ":"))
        self.disease_type_filter = QComboBox()
        self.disease_type_filter.addItem(tr("all_types"), None)
        self.load_disease_types()
        filter_row.addWidget(self.disease_type_filter)
        
        filter_row.addWidget(QLabel(tr("birth_year") + ":"))
        self.birth_year_filter = QLineEdit()
        self.birth_year_filter.setPlaceholderText(tr("year"))
        self.birth_year_filter.setMaximumWidth(80)
        filter_row.addWidget(self.birth_year_filter)
        
        search_layout.addLayout(filter_row)
        layout.addLayout(search_layout)
        
        # Search button
        button_layout = QHBoxLayout()
        
        self.search_button = QPushButton(f"🔎 {tr('find')}")
        self.search_button.setMinimumHeight(40)
        self.search_button.clicked.connect(self.perform_search)
        button_layout.addWidget(self.search_button)
        
        self.clear_button = QPushButton(f"🗑️ {tr('clear')}")
        self.clear_button.setMinimumHeight(40)
        self.clear_button.clicked.connect(self.clear_search)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Results label
        self.results_label = QLabel(f"{tr('results')}: 0")
        results_font = QFont()
        results_font.setBold(True)
        self.results_label.setFont(results_font)
        layout.addWidget(self.results_label)
        
        # Results table
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
        
        self.setLayout(layout)
    
    def load_disease_types(self):
        """Load disease types for filter"""
        types = get_unique_disease_types()
        self.disease_type_filter.clear()
        self.disease_type_filter.addItem(tr("all_types"), None)
        for dtype in types:
            self.disease_type_filter.addItem(dtype, dtype)
    
    def refresh_data(self):
        """Refresh data"""
        self.load_disease_types()
        self.perform_search()
    
    def perform_search(self):
        """Perform search with all filters"""
        # Build search term from general search
        search_term = self.general_search.text().strip()
        
        # Build filters
        filters = {}
        
        status_filter = self.status_filter.currentData()
        if status_filter:
            filters['status'] = status_filter
        
        disease_type_filter = self.disease_type_filter.currentData()
        if disease_type_filter:
            filters['disease_type'] = disease_type_filter
        
        birth_year = self.birth_year_filter.text().strip()
        if birth_year:
            try:
                filters['birth_year'] = int(birth_year)
            except ValueError:
                pass
        
        # If disease search is specified, add to search term
        disease_search = self.disease_search.text().strip()
        if disease_search:
            if search_term:
                search_term += f" {disease_search}"
            else:
                search_term = disease_search
        
        # Perform search
        self.patients, total_count = patient_service.search_patients(
            search_term, filters, page=1, page_size=1000
        )
        
        self.results_label.setText(f"{tr('results')}: {total_count}")
        self.update_table()
    
    def clear_search(self):
        """Clear all search fields"""
        self.general_search.clear()
        self.disease_search.clear()
        self.status_filter.setCurrentIndex(0)
        self.disease_type_filter.setCurrentIndex(0)
        self.birth_year_filter.clear()
        self.patients = []
        self.results_label.setText(f"{tr('results')}: 0")
        self.update_table()
    
    def update_table(self):
        """Update table with search results"""
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
            status_item = QTableWidgetItem(get_status_display(patient.treatment_status))
            self.table.setItem(row, 6, status_item)
            
            # Registration date
            self.table.setItem(row, 7, QTableWidgetItem(format_date(patient.registration_date)))
    
    def edit_patient(self):
        """Edit selected patient"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        patient_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        patient = patient_service.get_patient_by_id(patient_id)
        
        if patient:
            dialog = PatientDialog(self.user, patient, parent=self)
            if dialog.exec():
                self.perform_search()
    
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
        """)
    
    def update_language(self):
        """Update UI language"""
        # Update title
        # Find title label and update
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and "🔍" in widget.text():
                widget.setText(f"🔍 {tr('advanced_search')}")
                break
        
        # Update buttons
        self.search_button.setText(f"🔎 {tr('find')}")
        self.clear_button.setText(f"🗑️ {tr('clear')}")
        
        # Update results label
        self.results_label.setText(f"{tr('results')}: {len(self.patients)}")
        
        # Update table headers
        self.table.setHorizontalHeaderLabels([
            tr("hdr_id"), tr("hdr_full_name"), tr("hdr_phone"), tr("hdr_birth_year"), 
            tr("hdr_disease_type"), tr("hdr_disease_name"), tr("hdr_status"), tr("hdr_registration_date")
        ])
        
        # Update filters
        current_status = self.status_filter.currentIndex()
        self.status_filter.clear()
        self.status_filter.addItem(tr("all_statuses"), None)
        for status in TreatmentStatus:
            self.status_filter.addItem(get_status_display(status), status)
        self.status_filter.setCurrentIndex(current_status)
        
        # Update disease types
        self.load_disease_types()
