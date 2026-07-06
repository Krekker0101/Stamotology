"""
Statistics view UI for Laboratory Management System
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config
from services.statistics import statistics_service
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class StatisticsView(QWidget):
    """View for displaying statistics and charts"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("📊 Статистика")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # General statistics tab
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, config.get_translation('general_statistics'))
        
        # Treatment statistics tab
        self.treatment_tab = self.create_treatment_tab()
        self.tab_widget.addTab(self.treatment_tab, config.get_translation('treatment'))
        
        # Disease statistics tab
        self.disease_tab = self.create_disease_tab()
        self.tab_widget.addTab(self.disease_tab, config.get_translation('diseases'))
        
        # Activity tab
        self.activity_tab = self.create_activity_tab()
        self.tab_widget.addTab(self.activity_tab, "Активность")
        
        layout.addWidget(self.tab_widget)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        
        self.refresh_button = QPushButton("🔄 Обновить")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh_data)
        refresh_layout.addWidget(self.refresh_button)
        
        layout.addLayout(refresh_layout)
        self.setLayout(layout)
    
    def create_general_tab(self) -> QWidget:
        """Create general statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stats grid
        self.general_stats_grid = QGridLayout()
        layout.addLayout(self.general_stats_grid)
        
        # Chart
        self.general_chart_frame = QFrame()
        self.general_chart_layout = QVBoxLayout()
        self.general_chart_frame.setLayout(self.general_chart_layout)
        layout.addWidget(self.general_chart_frame)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_treatment_tab(self) -> QWidget:
        """Create treatment statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stats grid
        self.treatment_stats_grid = QGridLayout()
        layout.addLayout(self.treatment_stats_grid)
        
        # Chart
        self.treatment_chart_frame = QFrame()
        self.treatment_chart_layout = QVBoxLayout()
        self.treatment_chart_frame.setLayout(self.treatment_chart_layout)
        layout.addWidget(self.treatment_chart_frame)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_disease_tab(self) -> QWidget:
        """Create disease statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Chart
        self.disease_chart_frame = QFrame()
        self.disease_chart_layout = QVBoxLayout()
        self.disease_chart_frame.setLayout(self.disease_chart_layout)
        layout.addWidget(self.disease_chart_frame)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_activity_tab(self) -> QWidget:
        """Create activity statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Chart
        self.activity_chart_frame = QFrame()
        self.activity_chart_layout = QVBoxLayout()
        self.activity_chart_frame.setLayout(self.activity_chart_layout)
        layout.addWidget(self.activity_chart_frame)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def refresh_data(self):
        """Refresh all statistics data"""
        self.load_general_statistics()
        self.load_treatment_statistics()
        self.load_disease_statistics()
        self.load_activity_statistics()
    
    def load_general_statistics(self):
        """Load general statistics"""
        stats = statistics_service.get_general_statistics()
        
        # Clear grid
        while self.general_stats_grid.count():
            item = self.general_stats_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add stat cards
        stat_items = [
            ("Всего пациентов", stats.get('total', 0)),
            ("Новых за месяц", stats.get('new_this_month', 0)),
            ("Новых за год", stats.get('new_this_year', 0)),
        ]
        
        for i, (label, value) in enumerate(stat_items):
            card = self.create_stat_card(label, str(value))
            self.general_stats_grid.addWidget(card, 0, i)
        
        # Create status chart
        self.create_status_chart(stats.get('by_status', {}))
    
    def create_stat_card(self, label: str, value) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet("background-color: #f5f5f5; border-radius: 5px; padding: 10px;")
        
        layout = QVBoxLayout()
        
        label_widget = QLabel(label)
        label_font = QFont()
        label_font.setPointSize(9)
        label_widget.setFont(label_font)
        layout.addWidget(label_widget)
        
        # Convert value to string
        value_str = str(value)
        value_widget = QLabel(value_str)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_widget.setFont(value_font)
        layout.addWidget(value_widget)
        
        card.setLayout(layout)
        return card
    
    def create_status_chart(self, status_data: dict):
        """Create status distribution chart"""
        # Clear previous chart and close figures
        while self.general_chart_layout.count():
            item = self.general_chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                if hasattr(widget, 'figure'):
                    plt.close(widget.figure)
        
        # Create matplotlib figure
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        labels = []
        values = []
        colors = []
        
        for status, count in status_data.items():
            labels.append(config.get_status_display(status).split(' ', 1)[1] if ' ' in config.get_status_display(status) else status)
            values.append(count)
            colors.append(config.get_status_color(status))
        
        if values:
            ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title(config.get_translation('status_distribution'))
        
        canvas = FigureCanvas(fig)
        self.general_chart_layout.addWidget(canvas)
    
    def load_treatment_statistics(self):
        """Load treatment statistics"""
        stats = statistics_service.get_treatment_statistics()
        
        # Clear grid
        while self.treatment_stats_grid.count():
            item = self.treatment_stats_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add stat cards
        stat_items = [
            (config.get_translation('completed_treatment'), stats.get('completed_count', 0)),
            (config.get_translation('avg_treatment_days'), f"{stats.get('avg_treatment_days', 0):.1f}"),
        ]
        
        for i, (label, value) in enumerate(stat_items):
            card = self.create_stat_card(label, value)
            self.treatment_stats_grid.addWidget(card, 0, i)
        
        # Create doctor chart
        self.create_doctor_chart(stats.get('by_doctor', {}))
    
    def create_doctor_chart(self, doctor_data: dict):
        """Create doctor performance chart"""
        # Clear previous chart and close figures
        while self.treatment_chart_layout.count():
            item = self.treatment_chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                if hasattr(widget, 'figure'):
                    plt.close(widget.figure)
        
        # Create matplotlib figure
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        doctors = list(doctor_data.keys())[:10]  # Top 10
        values = [doctor_data.get(doc, 0) for doc in doctors]
        
        if values:
            ax.barh(doctors, values)
            ax.set_xlabel(config.get_translation('total_patients'))
            ax.set_title(config.get_translation('patients_by_doctor'))
        
        canvas = FigureCanvas(fig)
        self.treatment_chart_layout.addWidget(canvas)
    
    def load_disease_statistics(self):
        """Load disease statistics"""
        stats = statistics_service.get_disease_statistics()
        
        # Create disease type chart
        self.create_disease_type_chart(stats.get('by_type', {}))
    
    def create_disease_type_chart(self, disease_data: dict):
        """Create disease type chart"""
        # Clear previous chart and close figures
        while self.disease_chart_layout.count():
            item = self.disease_chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                if hasattr(widget, 'figure'):
                    plt.close(widget.figure)
        
        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        diseases = list(disease_data.keys())[:10]  # Top 10
        values = [disease_data.get(d, 0) for d in diseases]
        
        if values:
            ax.barh(diseases, values)
            ax.set_xlabel(config.get_translation('total_patients'))
            ax.set_title(config.get_translation('disease_distribution'))
        
        canvas = FigureCanvas(fig)
        self.disease_chart_layout.addWidget(canvas)
    
    def load_activity_statistics(self):
        """Load activity statistics"""
        stats = statistics_service.get_activity_statistics(days=30)
        
        # Create activity chart
        self.create_activity_chart(stats.get('daily_activity', {}))
    
    def create_activity_chart(self, activity_data: dict):
        """Create daily activity chart"""
        # Clear previous chart
        while self.activity_chart_layout.count():
            item = self.activity_chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Create matplotlib figure
        fig = Figure(figsize=(8, 4))
        ax = fig.add_subplot(111)
        
        dates = list(activity_data.keys())[-30:]  # Last 30 days
        values = [activity_data.get(d, 0) for d in dates]
        
        if values:
            ax.plot(range(len(dates)), values, marker='o')
            ax.set_xlabel('Дни')
            ax.set_ylabel('Количество действий')
            ax.set_title('Активность за последние 30 дней')
            ax.set_xticks(range(0, len(dates), 5))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), 5)], rotation=45)
        
        canvas = FigureCanvas(fig)
        self.activity_chart_layout.addWidget(canvas)
    
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
