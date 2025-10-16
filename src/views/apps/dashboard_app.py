from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFrame, QGridLayout, QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from views.apps.base_app import BaseApp

class DashboardApp(BaseApp):
    """Dashboard principal con resumen del sistema"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_data()
        
    def get_title(self):
        return "Dashboard"
        
    def get_icon(self):
        return "📊"
        
    def setup_ui(self):
        """Configurar la interfaz del dashboard"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("📊 Dashboard del Sistema")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title)
        
        # Grid de métricas
        metrics_grid = self.create_metrics_grid()
        layout.addLayout(metrics_grid)
        
        # Gráficos/estadísticas
        charts_section = self.create_charts_section()
        layout.addWidget(charts_section)
        
        # Actividad reciente
        activity_section = self.create_activity_section()
        layout.addWidget(activity_section)
        
        layout.addStretch()
        
    def create_metrics_grid(self):
        """Crear grid de métricas principales"""
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Métrica 1: Libros totales
        metric1 = self.create_metric_card("📚 Libros Totales", "15", "#3498db", "+2 este mes")
        grid.addWidget(metric1, 0, 0)
        
        # Métrica 2: Consultas IA
        metric2 = self.create_metric_card("🤖 Consultas IA", "47", "#9b59b6", "+12 esta semana")
        grid.addWidget(metric2, 0, 1)
        
        # Métrica 3: Espacio usado
        metric3 = self.create_metric_card("💾 Espacio Usado", "125 MB", "#e74c3c", "de 1 GB")
        grid.addWidget(metric3, 1, 0)
        
        # Métrica 4: Tiempo activo
        metric4 = self.create_metric_card("⏰ Tiempo Activo", "28 días", "#2ecc71", "sin interrupciones")
        grid.addWidget(metric4, 1, 1)
        
        return grid
        
    def create_metric_card(self, title: str, value: str, color: str, subtitle: str = ""):
        """Crear una tarjeta de métrica individual"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
                background-color: #f8f9fa;
            }}
        """)
        card.setMinimumHeight(120)
        
        layout = QVBoxLayout(card)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {color};
            }}
        """)
        layout.addWidget(value_label)
        
        # Subtítulo
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #95a5a6;
                }
            """)
            layout.addWidget(subtitle_label)
        
        layout.addStretch()
        return card
        
    def create_charts_section(self):
        """Crear sección de gráficos (simulados)"""
        section = QGroupBox("📈 Estadísticas de Uso")
        section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
        """)
        
        layout = QHBoxLayout(section)
        
        # Gráfico simulado 1
        chart1 = self.create_simulated_chart("Consultas por Día", ["Lun", "Mar", "Mié", "Jue", "Vie"], [5, 8, 12, 9, 15])
        layout.addWidget(chart1)
        
        # Gráfico simulado 2
        chart2 = self.create_simulated_chart("Libros por Tipo", ["PDF", "DOC", "TXT"], [12, 2, 1])
        layout.addWidget(chart2)
        
        return section
        
    def create_simulated_chart(self, title: str, labels: list, values: list):
        """Crear un gráfico simulado"""
        chart = QFrame()
        chart.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        chart.setFixedSize(250, 200)
        
        layout = QVBoxLayout(chart)
        
        # Título del gráfico
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Barras simuladas
        for i, (label, value) in enumerate(zip(labels, values)):
            bar_container = QHBoxLayout()
            
            label_widget = QLabel(label)
            label_widget.setFixedWidth(30)
            label_widget.setStyleSheet("font-size: 11px; color: #7f8c8d;")
            
            # Barra de progreso simulada
            bar = QProgressBar()
            bar.setValue(min(value * 10, 100))  # Escalar valores
            bar.setTextVisible(False)
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    background-color: #ecf0f1;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    border-radius: 2px;
                }
            """)
            
            value_label = QLabel(str(value))
            value_label.setStyleSheet("font-size: 11px; color: #2c3e50; font-weight: bold;")
            value_label.setFixedWidth(20)
            
            bar_container.addWidget(label_widget)
            bar_container.addWidget(bar)
            bar_container.addWidget(value_label)
            
            layout.addLayout(bar_container)
        
        layout.addStretch()
        return chart
        
    def create_activity_section(self):
        """Crear sección de actividad reciente"""
        section = QGroupBox("🕒 Actividad Reciente")
        section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        # Actividades
        activities = [
            ("📥", "Nuevo libro agregado: 'Derecho Civil.pdf'", "Hace 2 horas"),
            ("🔍", "Consulta IA realizada sobre 'Propiedad Intelectual'", "Hace 5 horas"),
            ("⚡", "Vectores generados para 3 libros", "Ayer"),
            ("📊", "Reporte mensual generado", "Hace 2 días")
        ]
        
        for icon, text, time in activities:
            activity_item = self.create_activity_item(icon, text, time)
            layout.addWidget(activity_item)
        
        return section
        
    def create_activity_item(self, icon: str, text: str, time: str):
        """Crear un ítem de actividad"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 10px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(item)
        
        # Icono
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(30)
        
        # Texto
        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
        text_label.setWordWrap(True)
        
        # Tiempo
        time_label = QLabel(time)
        time_label.setStyleSheet("font-size: 11px; color: #95a5a6;")
        time_label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(time_label)
        
        return item
        
    def setup_data(self):
        """Configurar datos del dashboard (simulados)"""
        # Aquí podrías cargar datos reales de tu base de datos
        pass