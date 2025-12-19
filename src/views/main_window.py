from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QFrame, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from views.sidebar import Sidebar
from views.styles import apply_light_theme

class MainWindow(QMainWindow):
    """Ventana principal con sistema de navegación"""
    
    def __init__(self, nav_controller):
        super().__init__()
        self.nav_controller = nav_controller
        self.current_app_widget = None
        
        # Calcular factor de escala dinámico
        from views.styles import get_scale_factor
        self.scale_factor = get_scale_factor(self)
        print(f"📏 Factor de escala detectado: {self.scale_factor}")
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Configurar la interfaz de usuario principal"""
        self.setWindowTitle("Sistema Biblioteca IA - Dashboard")
        
        # Dimensiones dinámicas basadas en escala
        width = int(1500 * self.scale_factor)
        height = int(950 * self.scale_factor)
        min_w = int(1200 * self.scale_factor)
        min_h = int(800 * self.scale_factor)
        
        self.setGeometry(100, 100, width, height)
        self.setMinimumSize(min_w, min_h)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra lateral
        self.sidebar = Sidebar(self.nav_controller)
        main_layout.addWidget(self.sidebar)
        
        # Área de contenido principal
        self.content_area = self.create_content_area()
        main_layout.addWidget(self.content_area)
        
    def create_content_area(self):
        """Crear el área de contenido principal"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header del área de contenido
        header = self.create_content_header()
        layout.addWidget(header)
        
        # Widget apilado para cambiar entre aplicaciones
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        return container
        
    def create_content_header(self):
        """Crear el header del área de contenido"""
        header = QFrame()
        header.setFixedHeight(int(60 * self.scale_factor))
        header.setStyleSheet(f"""
            QFrame {{
                background-color: #2c3e50;
                border-bottom: 1px solid #34495e;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Título de la aplicación actual
        self.app_title = QLabel("Sistema Biblioteca IA")
        self.app_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {int(20 * self.scale_factor)}px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.app_title)
        
        # Espacio flexible
        layout.addStretch()
        
        # Información del usuario
        self.user_info = QLabel("Modo: Desktop • v1.0.0")
        self.user_info.setStyleSheet(f"""
            QLabel {{
                color: #bdc3c7;
                font-size: {int(14 * self.scale_factor)}px;
            }}
        """)
        layout.addWidget(self.user_info)
        
        return header
        
    def on_app_changed(self, app_name: str):
        """Cuando se cambia de aplicación desde la barra lateral"""
        app = self.nav_controller.get_app(app_name)
        if app:
            self.show_app(app)
            
    def show_app(self, app):
        """Mostrar una aplicación específica"""
        # Limpiar aplicación anterior si existe
        if self.current_app_widget:
            self.stacked_widget.removeWidget(self.current_app_widget)
            
        # Agregar nueva aplicación
        self.stacked_widget.addWidget(app)
        self.current_app_widget = app
        
        # Actualizar título
        self.app_title.setText(app.get_title())
        
        # Mostrar la aplicación
        self.stacked_widget.setCurrentWidget(app)
        
    def apply_styles(self):
        """Aplicar estilos a la aplicación"""
        apply_light_theme(self)

    def on_app_changed(self, app_name: str):
        """Cuando se cambia de aplicación desde la barra lateral"""
        print(f"🔄 MainWindow: Cambiando a aplicación: {app_name}")  # Debug
        app = self.nav_controller.get_app(app_name)
        if app:
            self.show_app(app)
        else:
            print(f"❌ MainWindow: No se encontró la aplicación: {app_name}")