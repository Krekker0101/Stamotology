"""
Statistics view UI for Laboratory Management System
Modernized: seaborn styles, Qt6 matplotlib backend, export and toolbar,
optimized queries usage from statistics_service.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFrame, QGridLayout, QFileDialog, QMessageBox,
    QTableWidget, QHeaderView, QTableWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import copy
import config
from config import get_status_display, get_status_color
from services.statistics import statistics_service
from i18n import tr

# Use Qt6-compatible backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Disable pickle support to avoid deepcopy recursion issues
matplotlib.rcParams['figure.max_open_warning'] = 0
matplotlib.rcParams['agg.path.chunksize'] = 0  # Disable path chunking to prevent deepcopy issues
matplotlib.rcParams['axes.grid'] = True
matplotlib.rcParams['grid.alpha'] = 0.25
matplotlib.rcParams['axes.facecolor'] = '#f8f9fa'
matplotlib.rcParams['figure.facecolor'] = '#ffffff'

_original_deepcopy = copy.deepcopy


def _matplotlib_safe_deepcopy(obj, memo=None):
    if hasattr(obj, '__module__') and obj.__module__ and 'matplotlib' in obj.__module__:
        return obj
    return _original_deepcopy(obj, memo or {})


copy.deepcopy = _matplotlib_safe_deepcopy


class StatisticsView(QWidget):
    """View for displaying statistics and charts with modern look"""

    def __init__(self):
        super().__init__()
        plt.rcParams.update({
            'figure.titlesize': 14,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'legend.fontsize': 9,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
        })
        
        # Create persistent figure objects to avoid deepcopy recursion
        self.trend_fig = Figure(figsize=(6, 3), dpi=100)
        self.trend_ax = self.trend_fig.add_subplot(111)
        self.trend_canvas = FigureCanvas(self.trend_fig)
        
        self.status_fig = Figure(figsize=(4, 3), dpi=100)
        self.status_ax = self.status_fig.add_subplot(111)
        self.status_canvas = FigureCanvas(self.status_fig)
        
        self.top_diseases_fig = Figure(figsize=(4, 3), dpi=100)
        self.top_diseases_ax = self.top_diseases_fig.add_subplot(111)
        self.top_diseases_canvas = FigureCanvas(self.top_diseases_fig)
        
        self.doctor_fig = Figure(figsize=(8, 3), dpi=100)
        self.doctor_ax = self.doctor_fig.add_subplot(111)
        self.doctor_canvas = FigureCanvas(self.doctor_fig)
        
        self.disease_type_fig = Figure(figsize=(8, 4), dpi=100)
        self.disease_type_ax = self.disease_type_fig.add_subplot(111)
        self.disease_type_canvas = FigureCanvas(self.disease_type_fig)
        
        self.activity_fig = Figure(figsize=(8, 3), dpi=100)
        self.activity_ax = self.activity_fig.add_subplot(111)
        self.activity_canvas = FigureCanvas(self.activity_fig)
        
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel(f"📊 {tr('general_statistics')}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Tab widget
        self.tab_widget = QTabWidget()

        # General statistics tab
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, tr('general_statistics'))

        # Treatment statistics tab
        self.treatment_tab = self.create_treatment_tab()
        self.tab_widget.addTab(self.treatment_tab, tr('treatment_statistics'))

        # Disease statistics tab
        self.disease_tab = self.create_disease_tab()
        self.tab_widget.addTab(self.disease_tab, tr('diseases'))

        # Activity tab
        self.activity_tab = self.create_activity_tab()
        self.tab_widget.addTab(self.activity_tab, tr('activity'))

        # Doctor-patient report tab
        self.doctor_report_tab = self.create_doctor_report_tab()
        self.tab_widget.addTab(self.doctor_report_tab, "Пациенты по врачам")

        # Connect tab change signal to load data when switching to doctor report tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

        # Controls: refresh + export
        controls_layout = QHBoxLayout()
        self.refresh_button = QPushButton("🔄 " + tr('general_statistics'))
        self.refresh_button.setMinimumHeight(36)
        self.refresh_button.clicked.connect(self.refresh_data)
        controls_layout.addWidget(self.refresh_button)

        controls_layout.addStretch()

        self.export_button = QPushButton("📤 " + tr('export'))
        self.export_button.setMinimumHeight(36)
        self.export_button.clicked.connect(self.export_all_figures)
        controls_layout.addWidget(self.export_button)

        layout.addLayout(controls_layout)

        self.setLayout(layout)

    def create_general_tab(self) -> QWidget:
        """Create general statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Summary cards
        self.general_stats_grid = QGridLayout()
        self.general_stats_grid.setSpacing(12)
        layout.addLayout(self.general_stats_grid)

        # Chart area split into two columns
        chart_row = QHBoxLayout()

        # Left: monthly trend
        self.trend_frame = QFrame()
        self.trend_layout = QVBoxLayout()
        self.trend_frame.setLayout(self.trend_layout)
        chart_row.addWidget(self.trend_frame, 2)

        # Right: status pie + top diseases
        right_col = QVBoxLayout()
        self.status_frame = QFrame()
        self.status_layout = QVBoxLayout()
        self.status_frame.setLayout(self.status_layout)
        right_col.addWidget(self.status_frame)

        self.top_diseases_frame = QFrame()
        self.top_diseases_layout = QVBoxLayout()
        self.top_diseases_frame.setLayout(self.top_diseases_layout)
        right_col.addWidget(self.top_diseases_frame)

        chart_row.addLayout(right_col, 1)

        layout.addLayout(chart_row)

        widget.setLayout(layout)
        return widget

    def create_treatment_tab(self) -> QWidget:
        """Create treatment statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        self.treatment_stats_grid = QGridLayout()
        layout.addLayout(self.treatment_stats_grid)

        self.treatment_chart_frame = QFrame()
        self.treatment_chart_layout = QVBoxLayout()
        self.treatment_chart_frame.setLayout(self.treatment_chart_layout)
        layout.addWidget(self.treatment_chart_frame)

        widget.setLayout(layout)
        return widget

    def create_disease_tab(self) -> QWidget:
        """Create disease statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.disease_chart_frame = QFrame()
        self.disease_chart_layout = QVBoxLayout()
        self.disease_chart_frame.setLayout(self.disease_chart_layout)
        layout.addWidget(self.disease_chart_frame)

        widget.setLayout(layout)
        return widget

    def create_activity_tab(self) -> QWidget:
        """Create activity statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.activity_chart_frame = QFrame()
        self.activity_chart_layout = QVBoxLayout()
        self.activity_chart_frame.setLayout(self.activity_chart_layout)
        layout.addWidget(self.activity_chart_frame)

        widget.setLayout(layout)
        return widget

    def create_doctor_report_tab(self) -> QWidget:
        """Create doctor-patient report tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section with icon
        header_layout = QHBoxLayout()
        icon_label = QLabel("👨‍⚕️")
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        
        title_label = QLabel("Пациенты по врачам")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Info label with modern styling
        info_label = QLabel("📋 Выберите врача из списка, чтобы посмотреть список его пациентов")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                color: #1565c0;
                padding: 12px;
                border-radius: 8px;
                border-left: 4px solid #1976d2;
                font-size: 11px;
            }
        """)
        layout.addWidget(info_label)

        # Doctors table with card styling
        doctors_card = QFrame()
        doctors_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        doctors_layout = QVBoxLayout()
        doctors_layout.setContentsMargins(15, 15, 15, 15)
        doctors_layout.setSpacing(10)

        doctors_title = QLabel("📊 Список врачей")
        doctors_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #37474f;")
        doctors_layout.addWidget(doctors_title)

        self.doctor_report_table = QTableWidget()
        self.doctor_report_table.setColumnCount(2)
        self.doctor_report_table.setHorizontalHeaderLabels(["Врач", "Пациентов"])
        self.doctor_report_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.doctor_report_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.doctor_report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.doctor_report_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.doctor_report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.doctor_report_table.itemSelectionChanged.connect(self._show_selected_doctor_patients)
        self.doctor_report_table.setStyleSheet("""
            QTableWidget {
                background-color: #fafafa;
                border: none;
                border-radius: 8px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #37474f;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.doctor_report_table.setAlternatingRowColors(True)
        self.doctor_report_table.verticalHeader().setVisible(False)
        self.doctor_report_table.setMinimumHeight(150)
        doctors_layout.addWidget(self.doctor_report_table)

        doctors_card.setLayout(doctors_layout)
        layout.addWidget(doctors_card)

        # Patients table with card styling
        patients_card = QFrame()
        patients_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        patients_layout = QVBoxLayout()
        patients_layout.setContentsMargins(15, 15, 15, 15)
        patients_layout.setSpacing(10)

        self.doctor_patients_label = QLabel("👥 Пациенты врача")
        self.doctor_patients_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #37474f;")
        patients_layout.addWidget(self.doctor_patients_label)

        self.doctor_patients_table = QTableWidget()
        self.doctor_patients_table.setColumnCount(2)
        self.doctor_patients_table.setHorizontalHeaderLabels(["ФИО пациента", "Дата регистрации"])
        self.doctor_patients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.doctor_patients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.doctor_patients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.doctor_patients_table.setStyleSheet("""
            QTableWidget {
                background-color: #fafafa;
                border: none;
                border-radius: 8px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #37474f;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.doctor_patients_table.setAlternatingRowColors(True)
        self.doctor_patients_table.verticalHeader().setVisible(False)
        self.doctor_patients_table.setMinimumHeight(200)
        patients_layout.addWidget(self.doctor_patients_table)

        patients_card.setLayout(patients_layout)
        layout.addWidget(patients_card)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ------------------ Data loaders ------------------
    def on_tab_changed(self, index):
        """Handle tab change event"""
        # Load doctor report data when switching to the doctor report tab (index 4)
        if index == 4:
            self.load_doctor_patient_report()

    def refresh_data(self):
        """Refresh all statistics data"""
        # Load and render each section; keep UI responsive by doing light-weight tasks
        self.load_general_statistics()
        self.load_treatment_statistics()
        self.load_disease_statistics()
        self.load_activity_statistics()
        self.load_doctor_patient_report()

    def load_general_statistics(self):
        stats = statistics_service.get_general_statistics()

        # Clear previous summary cards
        while self.general_stats_grid.count():
            item = self.general_stats_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Build summary cards (rich style)
        cards = [
            (tr('total_patients'), stats.get('total_patients', 0), "👥"),
            (tr('new_this_month'), stats.get('new_this_month', 0), "🆕"),
            (tr('new_this_year'), stats.get('new_this_year', 0), "📅"),
            (tr('avg_treatment_days'), f"{statistics_service.get_treatment_statistics().get('avg_treatment_days', 0):.1f}", "⏱️"),
        ]

        for i, (label, value, icon) in enumerate(cards):
            card = self._make_card(label, str(value), icon)
            self.general_stats_grid.addWidget(card, 0, i)

        # Trend chart (monthly)
        monthly = statistics_service.get_monthly_statistics()
        self._draw_monthly_trend(monthly)

        # Status pie
        treatment = statistics_service.get_treatment_statistics()
        self._draw_status_pie(treatment.get('status_distribution', {}))

        # Top diseases
        disease_stats = statistics_service.get_disease_statistics().get('by_name', {})
        self._draw_top_diseases(disease_stats)

    def load_treatment_statistics(self):
        stats = statistics_service.get_treatment_statistics()

        # Clear
        while self.treatment_stats_grid.count():
            item = self.treatment_stats_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        cards = [
            (tr('completed_treatment'), stats.get('completed_count', 0), "✅"),
            (tr('avg_treatment_days'), f"{stats.get('avg_treatment_days', 0):.1f}", "⏱️"),
        ]
        for i, (label, value, icon) in enumerate(cards):
            self.treatment_stats_grid.addWidget(self._make_card(label, str(value), icon), 0, i)

        # Doctor performance
        self._draw_doctor_performance(stats.get('by_doctor', {}))

    def load_disease_statistics(self):
        stats = statistics_service.get_disease_statistics()
        self._draw_disease_type_chart(stats.get('by_type', {}))

    def load_activity_statistics(self):
        stats = statistics_service.get_activity_statistics(days=30)
        self._draw_activity_chart(stats.get('daily_activity', {}))

    def load_doctor_patient_report(self):
        """Load doctor-patient report data"""
        report_data = statistics_service.get_doctor_patient_report()
        self._doctor_report_data = report_data

        self.doctor_report_table.setRowCount(len(report_data))
        for row, entry in enumerate(report_data):
            doctor_item = QTableWidgetItem(entry.get('doctor', ''))
            doctor_item.setData(Qt.ItemDataRole.UserRole, entry)
            self.doctor_report_table.setItem(row, 0, doctor_item)
            self.doctor_report_table.setItem(row, 1, QTableWidgetItem(str(entry.get('patient_count', 0))))

        if report_data:
            self.doctor_report_table.selectRow(0)
            self._show_selected_doctor_patients()
        else:
            self.doctor_patients_table.setRowCount(0)
            self.doctor_patients_label.setText("Нет данных")

    def _show_selected_doctor_patients(self):
        """Show list of patients for the currently selected doctor"""
        selected_rows = self.doctor_report_table.selectedItems()
        if not selected_rows:
            self.doctor_patients_table.setRowCount(0)
            self.doctor_patients_label.setText("Пациенты врача")
            return

        doctor_item = self.doctor_report_table.item(self.doctor_report_table.currentRow(), 0)
        if not doctor_item:
            return

        doctor_name = doctor_item.text()
        self.doctor_patients_label.setText(f"Пациенты врача: {doctor_name}")

        for entry in self._doctor_report_data:
            if entry.get('doctor') == doctor_name:
                patients = entry.get('patients', [])
                self.doctor_patients_table.setRowCount(len(patients))
                for row, patient in enumerate(patients):
                    self.doctor_patients_table.setItem(row, 0, QTableWidgetItem(patient.get('full_name', '')))
                    date_text = patient.get('registration_date')
                    if date_text:
                        if hasattr(date_text, 'strftime'):
                            date_text = date_text.strftime('%d.%m.%Y')
                        else:
                            date_text = str(date_text)
                    self.doctor_patients_table.setItem(row, 1, QTableWidgetItem(date_text or ''))
                break
        else:
            self.doctor_patients_table.setRowCount(0)

    # ------------------ Drawing helpers ------------------
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _make_card(self, title, value, icon="📊") -> QFrame:
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
                border-radius: 12px;
                padding: 16px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #e9ecef;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #e3f2fd);
                border: 1px solid #2196F3;
            }
        """)
        l = QVBoxLayout()
        l.setSpacing(8)
        
        # Icon and title row
        title_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(16)
        icon_label.setFont(icon_font)
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #6c757d;")
        
        title_row.addWidget(icon_label)
        title_row.addWidget(title_label)
        title_row.addStretch()
        
        # Value
        v = QLabel(value)
        vf = QFont()
        vf.setPointSize(24)
        vf.setBold(True)
        v.setFont(vf)
        v.setStyleSheet("color: #2196F3;")
        
        l.addLayout(title_row)
        l.addWidget(v)
        f.setLayout(l)
        return f

    def _draw_monthly_trend(self, monthly_stats: dict):
        self._clear_layout(self.trend_layout)
        # Clear and reuse persistent axes
        self.trend_ax.clear()
        
        # Prepare data
        months = list(range(1, 13))
        values = [monthly_stats.get(m, 0) for m in months]

        # Enhanced styling
        self.trend_ax.plot(months, values, marker='o', linewidth=3, 
                          markersize=8, color='#2196F3', 
                          markerfacecolor='#2196F3', markeredgecolor='#1976D2',
                          markeredgewidth=2, alpha=0.8)
        self.trend_ax.fill_between(months, values, alpha=0.3, color='#2196F3')
        self.trend_ax.set_xticks(months)
        self.trend_ax.set_xlabel(tr('month'), fontsize=10, fontweight='bold')
        self.trend_ax.set_ylabel(tr('total_patients'), fontsize=10, fontweight='bold')
        self.trend_ax.set_title(tr('general_statistics'), fontsize=12, fontweight='bold', pad=15)
        self.trend_ax.grid(True, alpha=0.3, linestyle='--')
        self.trend_ax.set_facecolor('#f8f9fa')
        self.trend_fig.patch.set_facecolor('#ffffff')
        self.trend_fig.tight_layout()

        toolbar = NavigationToolbar(self.trend_canvas, self)
        self.trend_layout.addWidget(toolbar)
        self.trend_layout.addWidget(self.trend_canvas)

    def _draw_status_pie(self, status_data: dict):
        self._clear_layout(self.status_layout)
        # Clear and reuse persistent axes
        self.status_ax.clear()

        labels = []
        sizes = []
        colors = []
        for status_key, cnt in status_data.items():
            # status_key might be like 'cured' or enum value
            label = get_status_display(status_key)
            labels.append(label if label else str(status_key))
            sizes.append(cnt)
            colors.append(get_status_color(status_key))

        if sum(sizes) == 0:
            self.status_ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center', 
                              fontsize=14, color='#6c757d')
        else:
            # Enhanced pie chart with shadow effect
            wedges, texts, autotexts = self.status_ax.pie(sizes, labels=labels, 
                                                          autopct='%1.1f%%', 
                                                          startangle=140, 
                                                          colors=colors,
                                                          shadow=True,
                                                          explode=[0.05] * len(sizes))
            for t in texts:
                t.set_fontsize(9)
                t.set_fontweight('bold')
            for t in autotexts:
                t.set_fontsize(8)
                t.set_fontweight('bold')
                t.set_color('white')
        self.status_ax.set_title(tr('result'), 
                                 fontsize=12, fontweight='bold', pad=15)
        self.status_fig.patch.set_facecolor('#ffffff')
        self.status_fig.tight_layout()

        self.status_layout.addWidget(self.status_canvas)

    def _draw_top_diseases(self, disease_data: dict):
        self._clear_layout(self.top_diseases_layout)
        # Clear and reuse persistent axes
        self.top_diseases_ax.clear()
        
        top = sorted(disease_data.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [t[0] for t in top]
        vals = [t[1] for t in top]

        # Enhanced horizontal bar chart with gradient colors
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(vals)))
        bars = self.top_diseases_ax.barh(labels[::-1], vals[::-1], color=colors[::-1])
        
        # Add value labels on bars
        for bar, val in zip(bars, vals[::-1]):
            width = bar.get_width()
            self.top_diseases_ax.text(width + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                                    f'{int(val)}', ha='left', va='center',
                                    fontsize=8, fontweight='bold')
        
        self.top_diseases_ax.set_title(tr('disease_distribution'),
                                       fontsize=12, fontweight='bold', pad=15)
        self.top_diseases_ax.set_xlabel(tr('quantity'), fontsize=10, fontweight='bold')
        self.top_diseases_ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        self.top_diseases_ax.set_facecolor('#f8f9fa')
        self.top_diseases_fig.patch.set_facecolor('#ffffff')
        self.top_diseases_fig.tight_layout()

        self.top_diseases_layout.addWidget(self.top_diseases_canvas)

    def _draw_doctor_performance(self, doctor_data: dict):
        self._clear_layout(self.treatment_chart_layout)
        # Clear and reuse persistent axes
        self.doctor_ax.clear()
        
        top = sorted(doctor_data.items(), key=lambda x: x[1], reverse=True)[:10]
        labels = [t[0] for t in top]
        vals = [t[1] for t in top]

        # Enhanced bar chart with gradient colors
        colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(vals)))
        bars = self.doctor_ax.bar(labels, vals, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # Add value labels on bars
        for bar, val in zip(bars, vals):
            height = bar.get_height()
            self.doctor_ax.text(bar.get_x() + bar.get_width()/2, height + max(vals)*0.01,
                              f'{int(val)}', ha='center', va='bottom',
                              fontsize=8, fontweight='bold')
        
        self.doctor_ax.set_title(tr('patients_by_doctor'),
                                fontsize=12, fontweight='bold', pad=15)
        self.doctor_ax.set_ylabel(tr('total_patients'),
                                  fontsize=10, fontweight='bold')
        self.doctor_ax.set_xlabel(tr('doctors'), fontsize=10, fontweight='bold')
        self.doctor_ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        self.doctor_ax.set_facecolor('#f8f9fa')
        self.doctor_fig.patch.set_facecolor('#ffffff')
        self.doctor_fig.tight_layout()

        toolbar = NavigationToolbar(self.doctor_canvas, self)
        self.treatment_chart_layout.addWidget(toolbar)
        self.treatment_chart_layout.addWidget(self.doctor_canvas)

    def _draw_disease_type_chart(self, disease_type_data: dict):
        self._clear_layout(self.disease_chart_layout)
        # Clear and reuse persistent axes
        self.disease_type_ax.clear()
        
        top = sorted(disease_type_data.items(), key=lambda x: x[1], reverse=True)[:12]
        labels = [t[0] for t in top]
        vals = [t[1] for t in top]

        # Enhanced horizontal bar chart with gradient colors
        colors = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(vals)))
        bars = self.disease_type_ax.barh(labels[::-1], vals[::-1], color=colors[::-1], alpha=0.85)
        
        # Add value labels on bars
        for bar, val in zip(bars, vals[::-1]):
            width = bar.get_width()
            self.disease_type_ax.text(width + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                                     f'{int(val)}', ha='left', va='center',
                                     fontsize=8, fontweight='bold')
        
        self.disease_type_ax.set_title(tr('disease_distribution'),
                                      fontsize=12, fontweight='bold', pad=15)
        self.disease_type_ax.set_xlabel(tr('quantity'), fontsize=10, fontweight='bold')
        self.disease_type_ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        self.disease_type_ax.set_facecolor('#f8f9fa')
        self.disease_type_fig.patch.set_facecolor('#ffffff')
        self.disease_type_fig.tight_layout()

        self.disease_chart_layout.addWidget(self.disease_type_canvas)

    def _draw_activity_chart(self, activity_data: dict):
        self._clear_layout(self.activity_chart_layout)
        # Clear and reuse persistent axes
        self.activity_ax.clear()
        
        dates = list(activity_data.keys())[-30:]
        vals = [activity_data.get(d, 0) for d in dates]

        # Enhanced line chart with area fill
        self.activity_ax.plot(range(len(dates)), vals, marker='o', linewidth=2.5,
                            markersize=6, color='#FF9800', 
                            markerfacecolor='#FF9800', markeredgecolor='#F57C00',
                            markeredgewidth=2, alpha=0.9)
        self.activity_ax.fill_between(range(len(dates)), vals, alpha=0.25, color='#FF9800')
        
        self.activity_ax.set_title(tr('activity_last_30_days'),
                                  fontsize=12, fontweight='bold', pad=15)
        self.activity_ax.set_xlabel(tr('days'), fontsize=10, fontweight='bold')
        self.activity_ax.set_ylabel(tr('actions'), fontsize=10, fontweight='bold')
        self.activity_ax.grid(True, alpha=0.3, linestyle='--')
        self.activity_ax.set_facecolor('#f8f9fa')
        self.activity_fig.patch.set_facecolor('#ffffff')
        self.activity_fig.tight_layout()

        toolbar = NavigationToolbar(self.activity_canvas, self)
        self.activity_chart_layout.addWidget(toolbar)
        self.activity_chart_layout.addWidget(self.activity_canvas)

    # ------------------ Export ------------------
    def export_all_figures(self):
        """Export visible figures to directory as PNGs"""
        dir_path = QFileDialog.getExistingDirectory(self, tr('select_folder'))
        if not dir_path:
            return
        try:
            # Save each canvas in current layouts
            saved = 0
            figures_to_save = []
            
            # Collect figures first without deepcopy
            for layout in [self.trend_layout, self.status_layout, self.top_diseases_layout, self.treatment_chart_layout, self.disease_chart_layout, self.activity_chart_layout]:
                for i in range(layout.count()):
                    w = layout.itemAt(i).widget()
                    if hasattr(w, 'figure'):
                        figures_to_save.append(w.figure)
            
            # Save figures directly
            for idx, fig in enumerate(figures_to_save):
                fname = f"report_{idx+1}.png"
                try:
                    fig.savefig(str(dir_path / fname), dpi=150, bbox_inches='tight')
                    saved += 1
                except Exception as e:
                    print(f"Error saving figure {idx+1}: {e}")
                    continue
            
            QMessageBox.information(self, tr('success'), tr('files_saved').format(count=saved, path=dir_path))
        except Exception as e:
            QMessageBox.critical(self, tr('error'), f'Не удалось экспортировать отчеты: {e}')

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
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
            }}
            QTabBar::tab {{
                background-color: {colors['surface']};
                color: {colors['text']};
                padding: 8px 16px;
                border: 1px solid {colors['border']};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['primary']};
                color: white;
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
            if isinstance(widget, QLabel) and "📊" in widget.text():
                widget.setText(f"📊 {tr('general_statistics')}")
                break
        
        # Update tab names
        self.tab_widget.setTabText(0, tr('general_statistics'))
        self.tab_widget.setTabText(1, tr('treatment_statistics'))
        self.tab_widget.setTabText(2, tr('diseases'))
        self.tab_widget.setTabText(3, tr('activity'))
        self.tab_widget.setTabText(4, tr('patients_by_doctor'))
        
        # Update buttons
        self.refresh_button.setText("🔄 " + tr('general_statistics'))
        self.export_button.setText("📤 " + tr('export'))
        
        # Refresh data to update chart labels
        self.refresh_data()
