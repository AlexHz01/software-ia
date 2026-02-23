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
        """Configurar la interfaz de usuario con navegación horizontal superior"""
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
        
        # Layout principal: VERTICAL para navegación superior
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de navegación (Ahora superior)
        self.sidebar = Sidebar(self.nav_controller)
        main_layout.addWidget(self.sidebar)
        
        # Área de contenido principal
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        
    def on_app_changed(self, app_name: str):
        """Cuando se cambia de aplicación desde la barra de navegación"""
        print(f"🔄 MainWindow: Cambiando a aplicación: {app_name}")
        app = self.nav_controller.get_app(app_name)
        if app:
            self.show_app(app)
        else:
            print(f"❌ MainWindow: No se encontró la aplicación: {app_name}")
            
    def show_app(self, app):
        """Mostrar una aplicación específica"""
        # Limpiar aplicación anterior si existe
        if self.current_app_widget:
            self.stacked_widget.removeWidget(self.current_app_widget)
            
        # Agregar nueva aplicación
        self.stacked_widget.addWidget(app)
        self.current_app_widget = app
        
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