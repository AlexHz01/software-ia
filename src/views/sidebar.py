from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class Sidebar(QWidget):
    """Barra de navegación horizontal con menú de aplicaciones"""
    
    def __init__(self, nav_controller):
        super().__init__()
        self.nav_controller = nav_controller
        self.app_buttons = {}
        
        # Factor de escala
        from views.styles import get_scale_factor
        self.scale_factor = get_scale_factor(self)
        
        self.setup_ui()
        
        # CONECTAR SEÑAL para actualizar cuando se registren apps
        self.nav_controller.apps_updated.connect(self.setup_app_buttons)
        
    def setup_ui(self):
        """Configurar la interfaz de la barra de navegación horizontal (Tema Claro)"""
        self.setFixedHeight(int(70 * self.scale_factor))
        self.setStyleSheet(f"""
            QWidget#NavigationBar {{
                background-color: #ffffff;
                border-bottom: 1px solid #dee2e6;
            }}
            QLabel {{
                color: #2c3e50;
                background: transparent;
            }}
        """)
        self.setObjectName("NavigationBar")
        
        # Layout horizontal principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)
        
        # 1. Logo y Título
        self.header = self.create_compact_header()
        layout.addWidget(self.header)
        
        # Separador vertical
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Plain)
        line.setFixedWidth(1)
        line.setStyleSheet("background-color: #dee2e6; margin: 15px 5px;")
        layout.addWidget(line)
        
        # 2. Contenedor de Botones (Horizontal)
        self.buttons_container = QWidget()
        self.buttons_container.setStyleSheet("background: transparent; border: none;")
        self.buttons_layout = QHBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(8)
        layout.addWidget(self.buttons_container)
        
        # Espacio flexible
        layout.addStretch()
        
        # 3. Info de versión o estado
        self.info_label = QLabel("v1.0.1 • Edición Profesional")
        self.info_label.setStyleSheet(f"color: #95a5a6; font-size: {int(12 * self.scale_factor)}px;")
        layout.addWidget(self.info_label)

    def create_compact_header(self):
        """Crear el header compacto para la versión horizontal"""
        header = QWidget()
        header.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        logo = QLabel("📚")
        logo.setStyleSheet(f"font-size: {int(24 * self.scale_factor)}px;")
        layout.addWidget(logo)
        
        title = QLabel("BIBLIOTECA IA")
        title.setStyleSheet(f"""
            QLabel {{
                color: #2c3e50;
                font-size: {int(16 * self.scale_factor)}px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)
        layout.addWidget(title)
        
        return header
        
    def setup_app_buttons(self):
        """Configurar los botones de las aplicaciones"""
        self.clear_existing_buttons()
        
        apps = self.nav_controller.get_available_apps()
        for app_name, app in apps.items():
            self.add_app_button(app_name, app)

    def clear_existing_buttons(self):
        """Limpiar botones existentes"""
        for btn in self.app_buttons.values():
            btn.deleteLater()
        self.app_buttons.clear()

    def add_app_button(self, app_name: str, app):
        """Agregar un botón de aplicación horizontal"""
        btn = QPushButton(f"{app.get_icon()} {app.get_title()}")
        btn.setProperty("app_name", app_name)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Estilo del botón horizontal (Tema Claro)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #2c3e50;
                border: none;
                padding: {int(8 * self.scale_factor)}px {int(18 * self.scale_factor)}px;
                font-size: {int(14 * self.scale_factor)}px;
                border-radius: {int(5 * self.scale_factor)}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #f1f3f5;
                color: #3498db;
            }}
            QPushButton[active="true"] {{
                background-color: #e7f1f9;
                color: #3498db;
                font-weight: bold;
                border-bottom: 2px solid #3498db;
                border-radius: 0px;
            }}
        """)
        
        self.app_buttons[app_name] = btn
        btn.clicked.connect(lambda checked, name=app_name: self.on_app_clicked(name))
        self.buttons_layout.addWidget(btn)
        
    def on_app_clicked(self, app_name: str):
        """Manejar el click en una aplicación con feedback visual"""
        for btn in self.app_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        if app_name in self.app_buttons:
            active_btn = self.app_buttons[app_name]
            active_btn.setProperty("active", True)
            active_btn.style().unpolish(active_btn)
            active_btn.style().polish(active_btn)
        
        self.nav_controller.set_current_app(app_name)