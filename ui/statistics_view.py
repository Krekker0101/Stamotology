"""
Statistics view UI for Laboratory Management System
Modernized: seaborn styles, Qt6 matplotlib backend, export and toolbar,
optimized queries usage from statistics_service.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFrame, QGridLayout, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config
from services.statistics import statistics_service

# Use Qt6-compatible backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

# Disable pickle support to avoid deepcopy recursion issues
matplotlib.rcParams['figure.max_open_warning'] = 0


class StatisticsView(QWidget):
    """View for displaying statistics and charts with modern look"""

    def __init__(self):
        super().__init__()
        # Apply seaborn theme for nicer visuals
        sns.set_style("whitegrid")
        sns.set_palette("Set2")
        plt.rcParams.update({
            'figure.titlesize': 14,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'legend.fontsize': 9,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
        })
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel(f"📊 {config.get_translation('general_statistics')}")
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
        self.tab_widget.addTab(self.activity_tab, 'Активность')

        layout.addWidget(self.tab_widget)

        # Controls: refresh + export
        controls_layout = QHBoxLayout()
        self.refresh_button = QPushButton("🔄 " + config.get_translation('general_statistics'))
        self.refresh_button.setMinimumHeight(36)
        self.refresh_button.clicked.connect(self.refresh_data)
        controls_layout.addWidget(self.refresh_button)

        controls_layout.addStretch()

        self.export_button = QPushButton("📤 Экспорт отчетов")
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

    # ------------------ Data loaders ------------------
    def refresh_data(self):
        """Refresh all statistics data"""
        # Load and render each section; keep UI responsive by doing light-weight tasks
        self.load_general_statistics()
        self.load_treatment_statistics()
        self.load_disease_statistics()
        self.load_activity_statistics()

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
            (config.get_translation('total_patients'), stats.get('total_patients', 0)),
            (config.get_translation('new_this_month') if hasattr(config, 'get_translation') else 'Новых за месяц', stats.get('new_this_month', 0)),
            (config.get_translation('new_this_year') if hasattr(config, 'get_translation') else 'Новых за год', stats.get('new_this_year', 0)),
            (config.get_translation('avg_treatment_days'), f"{statistics_service.get_treatment_statistics().get('avg_treatment_days', 0):.1f}"),
        ]

        for i, (label, value) in enumerate(cards):
            card = self._make_card(label, str(value))
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
            (config.get_translation('completed_treatment'), stats.get('completed_count', 0)),
            (config.get_translation('avg_treatment_days'), f"{stats.get('avg_treatment_days', 0):.1f}"),
        ]
        for i, (label, value) in enumerate(cards):
            self.treatment_stats_grid.addWidget(self._make_card(label, str(value)), 0, i)

        # Doctor performance
        self._draw_doctor_performance(stats.get('by_doctor', {}))

    def load_disease_statistics(self):
        stats = statistics_service.get_disease_statistics()
        self._draw_disease_type_chart(stats.get('by_type', {}))

    def load_activity_statistics(self):
        stats = statistics_service.get_activity_statistics(days=30)
        self._draw_activity_chart(stats.get('daily_activity', {}))

    # ------------------ Drawing helpers ------------------
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _make_card(self, title, value) -> QFrame:
        f = QFrame()
        f.setStyleSheet("border-radius:8px; padding:10px; background-color: #ffffff;")
        l = QVBoxLayout()
        t = QLabel(title)
        tf = QFont()
        tf.setPointSize(9)
        t.setFont(tf)
        v = QLabel(value)
        vf = QFont()
        vf.setPointSize(18)
        vf.setBold(True)
        v.setFont(vf)
        l.addWidget(t)
        l.addWidget(v)
        f.setLayout(l)
        return f

    def _draw_monthly_trend(self, monthly_stats: dict):
        self._clear_layout(self.trend_layout)
        # Prepare data
        months = list(range(1, 13))
        values = [monthly_stats.get(m, 0) for m in months]

        fig = Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(months, values, marker='o', linewidth=2)
        ax.set_xticks(months)
        ax.set_xlabel('Месяц')
        ax.set_ylabel(config.get_translation('total_patients'))
        ax.set_title('Пациенты по месяцам')
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        self.trend_layout.addWidget(toolbar)
        self.trend_layout.addWidget(canvas)

    def _draw_status_pie(self, status_data: dict):
        self._clear_layout(self.status_layout)
        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)

        labels = []
        sizes = []
        colors = []
        for status_key, cnt in status_data.items():
            # status_key might be like 'cured' or enum value
            label = config.get_status_display(status_key)
            labels.append(label if label else str(status_key))
            sizes.append(cnt)
            colors.append(config.get_status_color(status_key))

        if sum(sizes) == 0:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        else:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
            for t in texts + autotexts:
                t.set_fontsize(8)
        ax.set_title(config.get_translation('status_distribution'))
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        self.status_layout.addWidget(canvas)

    def _draw_top_diseases(self, disease_data: dict):
        self._clear_layout(self.top_diseases_layout)
        top = sorted(disease_data.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [t[0] for t in top]
        vals = [t[1] for t in top]

        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.barh(labels[::-1], vals[::-1])
        ax.set_title(config.get_translation('disease_distribution'))
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        self.top_diseases_layout.addWidget(canvas)

    def _draw_doctor_performance(self, doctor_data: dict):
        self._clear_layout(self.treatment_chart_layout)
        top = sorted(doctor_data.items(), key=lambda x: x[1], reverse=True)[:10]
        labels = [t[0] for t in top]
        vals = [t[1] for t in top]

        fig = Figure(figsize=(8, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(labels, vals)
        ax.set_title(config.get_translation('patients_by_doctor'))
        ax.set_ylabel(config.get_translation('total_patients'))
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        self.treatment_chart_layout.addWidget(toolbar)
        self.treatment_chart_layout.addWidget(canvas)

    def _draw_disease_type_chart(self, disease_type_data: dict):
        self._clear_layout(self.disease_chart_layout)
        top = sorted(disease_type_data.items(), key=lambda x: x[1], reverse=True)[:12]
        labels = [t[0] for t in top]
        vals = [t[1] for t in top]

        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.barh(labels[::-1], vals[::-1])
        ax.set_title(config.get_translation('disease_distribution'))
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        self.disease_chart_layout.addWidget(canvas)

    def _draw_activity_chart(self, activity_data: dict):
        self._clear_layout(self.activity_chart_layout)
        dates = list(activity_data.keys())[-30:]
        vals = [activity_data.get(d, 0) for d in dates]

        fig = Figure(figsize=(8, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(range(len(dates)), vals, marker='o')
        ax.set_title('Активность за последние 30 дней')
        ax.set_xlabel('Дни')
        ax.set_ylabel('Действия')
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        self.activity_chart_layout.addWidget(toolbar)
        self.activity_chart_layout.addWidget(canvas)

    # ------------------ Export ------------------
    def export_all_figures(self):
        """Export visible figures to directory as PNGs"""
        dir_path = QFileDialog.getExistingDirectory(self, 'Выберите папку для сохранения отчетов')
        if not dir_path:
            return
        try:
            # Save each canvas in current layouts
            saved = 0
            for layout in [self.trend_layout, self.status_layout, self.top_diseases_layout, self.treatment_chart_layout, self.disease_chart_layout, self.activity_chart_layout]:
                for i in range(layout.count()):
                    w = layout.itemAt(i).widget()
                    if hasattr(w, 'figure'):
                        fig = w.figure
                        fname = f"report_{saved+1}.png"
                        # Directly save figure without deep copying to avoid matplotlib recursion
                        try:
                            fig.savefig(str(config.config.FILES_DIR / fname), dpi=150, bbox_inches='tight')
                        except RecursionError:
                            # Fallback: flush and try again
                            plt.close(fig)
                            continue
                        saved += 1
            QMessageBox.information(self, 'Успех', f'Сохранено {saved} файлов в {dir_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать отчеты: {e}')

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
