from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from views.styles import get_sidebar_style

class Sidebar(QWidget):
    """Barra lateral de navegación con menú de aplicaciones"""
    
    def __init__(self, nav_controller):
        super().__init__()
        self.nav_controller = nav_controller
        self.app_buttons = {}
        self.setup_ui()
        
        # CONECTAR SEÑAL para actualizar cuando se registren apps
        self.nav_controller.apps_updated.connect(self.setup_app_buttons)
        
    def setup_ui(self):
        """Configurar la interfaz de la barra lateral"""
        self.setFixedWidth(200)
        self.setStyleSheet(get_sidebar_style())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header de la barra lateral
        header = self.create_sidebar_header()
        layout.addWidget(header)
        
        # Área scrollable para las aplicaciones
        scroll_area = self.create_apps_area()
        layout.addWidget(scroll_area)
        
        # Footer de la barra lateral
        footer = self.create_sidebar_footer()
        layout.addWidget(footer)
        
    def create_apps_area(self):
        """Crear área scrollable para las aplicaciones"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #34495e;
            }
            QScrollBar:vertical {
                background-color: #2c3e50;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #46627f;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5d7a97;
            }
        """)
        
        # Widget contenedor de aplicaciones
        self.apps_widget = QWidget()
        self.apps_layout = QVBoxLayout(self.apps_widget)
        self.apps_layout.setContentsMargins(10, 10, 10, 10)
        self.apps_layout.setSpacing(5)
        
        # Título de la sección
        section_title = QLabel("APLICACIONES")
        section_title.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 11px;
                font-weight: bold;
                padding: 10px 5px 5px 5px;
            }
        """)
        self.apps_layout.addWidget(section_title)
        
        # Contenedor específico para los botones
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(5)
        
        # Agregar el contenedor de botones al layout principal
        self.apps_layout.addWidget(self.buttons_container)
        
        # Espacio flexible
        self.apps_layout.addStretch()
        
        scroll_area.setWidget(self.apps_widget)
        return scroll_area
        
    def create_sidebar_header(self):
        """Crear el header de la barra lateral"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 1px solid #46627f;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Logo y título
        logo_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel("📚")
        logo_label.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(logo_label)
        
        title_layout = QVBoxLayout()
        title = QLabel("Sistema IA")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        subtitle = QLabel("Biblioteca")
        subtitle.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-size: 10px;
            }
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        logo_layout.addLayout(title_layout)
        
        layout.addLayout(logo_layout)
        
        return header
        
    def create_sidebar_footer(self):
        """Crear el footer de la barra lateral"""
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-top: 1px solid #46627f;
            }
        """)
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # Información de versión
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
            }
        """)
        layout.addWidget(version_label)
        
        # Estado
        status_label = QLabel("● En línea")
        status_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(status_label)
        
        return footer
        
    def setup_app_buttons(self):
        """Configurar los botones de las aplicaciones"""
        # PRIMERO limpiar cualquier botón existente
        self.clear_existing_buttons()
        
        apps = self.nav_controller.get_available_apps()
        print(f"🔍 Sidebar: Configurando {len(apps)} aplicaciones")
        
        for app_name, app in apps.items():
            print(f"   - Agregando botón: {app_name} -> {app.get_title()}")
            self.add_app_button(app_name, app)

    def clear_existing_buttons(self):
        """Limpiar botones existentes"""
        for btn in self.app_buttons.values():
            btn.deleteLater()
        self.app_buttons.clear()

    def add_app_button(self, app_name: str, app):
        """Agregar un botón de aplicación a la barra lateral"""
        btn = QPushButton(f"{app.get_icon()} {app.get_title()}")
        btn.setProperty("app_name", app_name)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Estilo del botón
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                border: none;
                text-align: left;
                padding: 8px 12px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #46627f;
            }
            QPushButton:pressed {
                background-color: #4a6a8a;
            }
            QPushButton[active="true"] {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Guardar referencia al botón
        self.app_buttons[app_name] = btn
        
        # Conectar click
        btn.clicked.connect(lambda checked, name=app_name: self.on_app_clicked(name))
        
        # Agregar al contenedor de botones
        self.buttons_layout.addWidget(btn)
        
    def on_app_clicked(self, app_name: str):
        """Cuando se hace click en una aplicación"""
        print(f"🖱️ Sidebar: Click en aplicación: {app_name}")
        
        # Resetear estilo de todos los botones
        for btn in self.app_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # Estilizar botón activo
        if app_name in self.app_buttons:
            active_btn = self.app_buttons[app_name]
            active_btn.setProperty("active", True)
            active_btn.style().unpolish(active_btn)
            active_btn.style().polish(active_btn)
        
        # Cambiar aplicación
        self.nav_controller.set_current_app(app_name)