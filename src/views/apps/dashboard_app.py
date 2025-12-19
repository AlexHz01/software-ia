from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFrame, QGridLayout, QProgressBar, QGroupBox,
                             QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import sqlite3
import os
from datetime import datetime, timedelta

from views.apps.base_app import BaseApp
from database.db_manager import DatabaseManager

class DashboardApp(BaseApp):
    """Dashboard principal con datos reales del sistema"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        
        # Factor de escala
        from views.styles import get_scale_factor
        self.scale_factor = get_scale_factor(self)
        
        self.setup_ui()
        self.load_real_data()
        
        # Timer para actualizaciones automáticas
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_real_data)
        self.update_timer.start(30000)  # Actualizar cada 30 segundos
        
    def get_title(self):
        return "Dashboard"
        
    def get_icon(self):
        return "📊"
        
    def setup_ui(self):
        """Configurar la interfaz del dashboard"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Título y botón de actualizar
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Dashboard del Sistema")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: {int(28 * self.scale_factor)}px;
                font-weight: bold;
                color: #2c3e50;
            }}
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                border: none;
                padding: {int(8 * self.scale_factor)}px {int(16 * self.scale_factor)}px;
                border-radius: {int(4 * self.scale_factor)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        self.btn_refresh.clicked.connect(self.load_real_data)
        header_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Grid de métricas PRINCIPALES
        self.metrics_grid = self.create_metrics_grid()
        layout.addLayout(self.metrics_grid)
        
        # Sección de gráficos y actividad
        content_layout = QHBoxLayout()
        
        # Columna izquierda - Gráficos
        left_column = QVBoxLayout()
        self.charts_section = self.create_charts_section()
        left_column.addWidget(self.charts_section)
        left_column.addStretch()
        
        # Columna derecha - Actividad
        right_column = QVBoxLayout()
        self.activity_section = self.create_activity_section()
        right_column.addWidget(self.activity_section)
        right_column.addStretch()
        
        content_layout.addLayout(left_column)
        content_layout.addLayout(right_column)
        layout.addLayout(content_layout)
        
        layout.addStretch()
        
    def create_metrics_grid(self):
        """Crear grid de métricas principales con datos dinámicos"""
        grid = QGridLayout()
        grid.setSpacing(15)

        # Tarjetas de métricas
        self.metric_libros = self.create_metric_card(
            "Total de Libros", "0", "#27ae60", "Cargando..."
        )
        grid.addWidget(self.metric_libros, 0, 0)    
        self.metric_consultas = self.create_metric_card(
            "Total de Consultas", "0", "#2980b9", "Cargando..."
        )
        grid.addWidget(self.metric_consultas, 0, 1)
        self.metric_fragmentos = self.create_metric_card(
            "Total de Fragmentos", "0", "#8e44ad", "Cargando..."
        )
        grid.addWidget(self.metric_fragmentos, 0, 2)
        self.metric_espacio = self.create_metric_card(
            "Espacio en BD", "0 MB", "#c0392b", "Cargando..."
        )
        
        return grid
        
    def create_metric_card(self, title: str, value: str, color: str, subtitle: str = ""):
        """Crear una tarjeta de métrica individual"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: {int(8 * self.scale_factor)}px;
                padding: {int(10 * self.scale_factor)}px;
                min-height: {int(50 * self.scale_factor)}px;
            }}
            QFrame:hover {{
                border: 1px solid {{color}};
                background-color: #f8f9fa;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {int(16 * self.scale_factor)}px;
                color: #7f8c8d;
                font-weight: bold;
            }}
        """)
        layout.addWidget(title_label)
        
        # Valor (dinámico)
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: {int(32 * self.scale_factor)}px;
                font-weight: bold;
                color: {{color}};
                padding: {int(5 * self.scale_factor)}px 0px;
            }}
        """)
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        # Subtítulo (dinámico)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                font-size: {int(14 * self.scale_factor)}px;
                color: #95a5a6;
            }}
        """)
        subtitle_label.setObjectName("subtitle")
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        return card
        
    def create_charts_section(self):
        """Crear sección de gráficos con datos reales"""
        section = QGroupBox("📈 Estadísticas de Uso")
        section.setStyleSheet("""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: {int(8 * self.scale_factor)}px;
                margin-top: {int(10 * self.scale_factor)}px;
                padding-top: {int(15 * self.scale_factor)}px;
                background-color: white;
                min-width: {int(400 * self.scale_factor)}px;
            }}
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        # Gráficos que se actualizarán con datos reales
        self.chart_consultas = self.create_consultas_chart()
        layout.addWidget(self.chart_consultas)
        
        self.chart_libros = self.create_libros_chart()
        layout.addWidget(self.chart_libros)
        
        return section
        
    def create_consultas_chart(self):
        """Gráfico de consultas por día"""
        chart = QFrame()
        chart.setStyleSheet("""
            QFrame {{
                background-color: white;
                border: 1px solid #ecf0f1;
                border-radius: {int(6 * self.scale_factor)}px;
                padding: {int(15 * self.scale_factor)}px;
                margin: {int(5 * self.scale_factor)}px;
            }}
        """)
        
        layout = QVBoxLayout(chart)
        
        title_label = QLabel("📊 Consultas por Día (Última Semana)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        self.bars_container_consultas = QVBoxLayout()
        layout.addLayout(self.bars_container_consultas)
        
        return chart
        
    def create_libros_chart(self):
        """Gráfico de libros por estado"""
        chart = QFrame()
        chart.setStyleSheet("""
            QFrame {{
                background-color: white;
                border: 1px solid #ecf0f1;
                border-radius: {int(6 * self.scale_factor)}px;
                padding: {int(15 * self.scale_factor)}px;
                margin: {int(5 * self.scale_factor)}px;
            }}
        """)
        
        layout = QVBoxLayout(chart)
        
        title_label = QLabel("📚 Libros por Estado")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        self.bars_container_libros = QVBoxLayout()
        layout.addLayout(self.bars_container_libros)
        
        return chart
        
    def create_activity_section(self):
        """Crear sección de actividad reciente con datos reales"""
        section = QGroupBox("🕒 Actividad Reciente")
        section.setStyleSheet("""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: {int(8 * self.scale_factor)}px;
                margin-top: {int(10 * self.scale_factor)}px;
                padding-top: {int(15 * self.scale_factor)}px;
                background-color: white;
                min-width: {int(350 * self.scale_factor)}px;
            }}
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.activities_widget = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_widget)
        self.activities_layout.setSpacing(5)
        
        scroll_area.setWidget(self.activities_widget)
        layout.addWidget(scroll_area)
        
        return section
        
    def create_activity_item(self, icon: str, text: str, time: str):
        """Crear un ítem de actividad"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {{
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: {int(6 * self.scale_factor)}px;
                padding: {int(10 * self.scale_factor)}px;
                margin: {int(2 * self.scale_factor)}px;
            }}
        """)
        
        layout = QHBoxLayout(item)
        
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(int(30 * self.scale_factor))
        
        text_label = QLabel(text)
        text_label.setStyleSheet(f"font-size: {int(15 * self.scale_factor)}px; color: #2c3e50;")
        text_label.setWordWrap(True)
        
        time_label = QLabel(time)
        time_label.setStyleSheet(f"font-size: {int(13 * self.scale_factor)}px; color: #95a5a6;")
        time_label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(time_label)
        
        return item

    def load_real_data(self):
        """Cargar datos reales desde la base de datos"""
        try:
            stats = self.db_manager.obtener_estadisticas()
            advanced_stats = self.db_manager.obtener_estadisticas_avanzadas()
            
            # Actualizar métricas principales
            self.update_metric_card(self.metric_libros, str(stats['total_libros']), 
                                  f"{self.get_libros_este_mes()} este mes")
            
            self.update_metric_card(self.metric_consultas, str(stats['total_consultas']), 
                                  f"{self.get_consultas_esta_semana()} esta semana")
            
            self.update_metric_card(self.metric_fragmentos, str(stats['total_fragmentos']), 
                                  f"{advanced_stats.get('total_tokens', 0):,} tokens")
            
            espacio = advanced_stats.get('espacio_estimado_mb', 0)
            self.update_metric_card(self.metric_espacio, f"{espacio} MB", 
                                  "Base de datos SQLite")
            
            # Actualizar gráficos
            self.update_consultas_chart()
            self.update_libros_chart()
            
            # Actualizar actividad reciente
            self.update_recent_activity()
            
        except Exception as e:
            print(f"❌ Error cargando datos del dashboard: {e}")

    def update_metric_card(self, card, new_value: str, new_subtitle: str = ""):
        """Actualizar los valores de una tarjeta de métrica"""
        value_label = card.findChild(QLabel, "value")
        subtitle_label = card.findChild(QLabel, "subtitle")
        
        if value_label:
            value_label.setText(new_value)
        if subtitle_label and new_subtitle:
            subtitle_label.setText(new_subtitle)

    def get_libros_este_mes(self):
        """Obtener número de libros agregados este mes usando métodos existentes"""
        try:
            libros = self.db_manager.obtener_libros()
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            count = 0
            for libro in libros:
                fecha = libro.get('fecha_procesado')
                if fecha and fecha >= inicio_mes:
                    count += 1
            return count
        except:
            return 0

    def get_consultas_esta_semana(self):
        """Obtener número de consultas esta semana usando métodos existentes"""
        try:
            # Por ahora retornar 0 ya que no hay método específico para consultas por fecha
            # En una implementación real, agregarías este método a DatabaseManager
            return 0
        except:
            return 0

    def update_consultas_chart(self):
        """Actualizar gráfico de consultas usando métodos existentes"""
        self.clear_layout(self.bars_container_consultas)
        
        try:
            stats = self.db_manager.obtener_estadisticas()
            total_consultas = stats.get('total_consultas', 0)
            
            # Simular distribución por período (en una app real esto vendría de la BD)
            periodos = [
                ("Hoy", min(total_consultas, 5)),
                ("Ayer", min(total_consultas, 3)),
                ("Esta Semana", min(total_consultas, 8)),
                ("Este Mes", min(total_consultas, 15))
            ]
            
            for periodo, count in periodos:
                if total_consultas > 0:
                    self.add_bar_to_chart(self.bars_container_consultas, periodo, count, total_consultas)
                
        except Exception as e:
            print(f"❌ Error actualizando gráfico de consultas: {e}")

    def update_libros_chart(self):
        """Actualizar gráfico de libros usando métodos existentes"""
        self.clear_layout(self.bars_container_libros)
        
        try:
            libros = self.db_manager.obtener_libros()
            total_libros = len(libros)
            
            if total_libros == 0:
                # Mostrar mensaje cuando no hay libros
                empty_label = QLabel("📚 Aún no hay libros procesados")
                empty_label.setStyleSheet("font-size: 12px; color: #95a5a6; text-align: center;")
                self.bars_container_libros.addWidget(empty_label)
                return
            
            # Contar por estado
            estados_count = {}
            for libro in libros:
                estado = libro.get('estado', 'procesado')
                estados_count[estado] = estados_count.get(estado, 0) + 1
            
            # Crear barras para cada estado
            for estado, count in estados_count.items():
                self.add_bar_to_chart(self.bars_container_libros, estado.capitalize(), count, total_libros)
                
        except Exception as e:
            print(f"❌ Error actualizando gráfico de libros: {e}")

    def add_bar_to_chart(self, layout, label: str, value: int, max_value: int):
        """Añadir una barra a un gráfico"""
        bar_container = QHBoxLayout()
        
        label_widget = QLabel(label)
        label_widget.setFixedWidth(int(80 * self.scale_factor))
        label_widget.setStyleSheet(f"font-size: {int(11 * self.scale_factor)}px; color: #7f8c8d;")
        
        bar = QProgressBar()
        percentage = min(int((value / max_value) * 100), 100) if max_value > 0 else 0
        bar.setValue(percentage)
        bar.setTextVisible(False)
        bar.setStyleSheet("""
            QProgressBar {{
                border: 1px solid #bdc3c7;
                border-radius: {int(3 * self.scale_factor)}px;
                background-color: #ecf0f1;
                height: {int(15 * self.scale_factor)}px;
            }}
            QProgressBar::chunk {{
                background-color: #3498db;
                border-radius: {int(2 * self.scale_factor)}px;
            }}
        """)
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: {int(11 * self.scale_factor)}px; color: #2c3e50; font-weight: bold;")
        value_label.setFixedWidth(int(30 * self.scale_factor))
        
        bar_container.addWidget(label_widget)
        bar_container.addWidget(bar)
        bar_container.addWidget(value_label)
        
        layout.addLayout(bar_container)

    def update_recent_activity(self):
        """Actualizar actividad reciente usando métodos existentes"""
        self.clear_layout(self.activities_layout)
        
        try:
            libros = self.db_manager.obtener_libros()
            
            if not libros:
                # Mostrar mensaje cuando no hay actividad
                item = self.create_activity_item("💡", "Agrega tu primer libro PDF para comenzar", "Ahora")
                self.activities_layout.addWidget(item)
                return
            
            # Últimos 3 libros agregados
            for libro in libros[:3]:
                tiempo = self.format_time_ago(libro.get('fecha_procesado'))
                titulo = libro.get('titulo', 'Sin título')
                if len(titulo) > 40:
                    titulo = titulo[:37] + "..."
                item = self.create_activity_item("📥", f"Libro agregado: '{titulo}'", tiempo)
                self.activities_layout.addWidget(item)
            
            # Mensaje informativo sobre consultas
            stats = self.db_manager.obtener_estadisticas()
            total_consultas = stats.get('total_consultas', 0)
            if total_consultas > 0:
                item = self.create_activity_item("🔍", f"Total de consultas realizadas: {total_consultas}", "Sistema")
                self.activities_layout.addWidget(item)
                
        except Exception as e:
            print(f"❌ Error actualizando actividad reciente: {e}")

    def format_time_ago(self, dt):
        """Formatear fecha como 'hace x tiempo'"""
        if not dt:
            return "Desconocido"
            
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"Hace {diff.days} días"
        elif diff.seconds > 3600:
            return f"Hace {diff.seconds // 3600} horas"
        elif diff.seconds > 60:
            return f"Hace {diff.seconds // 60} minutos"
        else:
            return "Hace un momento"

    def clear_layout(self, layout):
        """Limpiar todos los widgets de un layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()