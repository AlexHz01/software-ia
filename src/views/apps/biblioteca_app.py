from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
                             QTextEdit, QLabel, QFrame, QGroupBox, QProgressBar,
                             QFileDialog, QMessageBox, QSplitter, QWidget)
from PyQt5.QtCore import Qt

from views.apps.base_app import BaseApp

class BibliotecaApp(BaseApp):
    """Aplicación de gestión de biblioteca con IA"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def get_title(self):
        return "Biblioteca IA"
        
    def get_icon(self):
        return "📚"
        
    def setup_ui(self):
        """Configurar la interfaz de la aplicación de biblioteca"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título de la aplicación
        title = QLabel("📚 Biblioteca IA - Gestión de Libros")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Descripción
        description = QLabel(
            "Sistema para gestionar tu biblioteca personal con inteligencia artificial. "
            "Sube libros PDF, genera vectores y realiza consultas inteligentes."
        )
        description.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 5px 0px 20px 0px;
            }
        """)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Contenedor principal
        main_container = QHBoxLayout()
        
        # Panel izquierdo - Acciones rápidas
        left_panel = self.create_actions_panel()
        main_container.addWidget(left_panel)
        
        # Panel derecho - Información
        right_panel = self.create_info_panel()
        main_container.addWidget(right_panel)
        
        layout.addLayout(main_container)
        
    def create_actions_panel(self):
        """Crear panel de acciones rápidas"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        panel.setFixedWidth(300)
        
        layout = QVBoxLayout(panel)
        
        # Título del panel
        title = QLabel("Acciones Rápidas")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Botón agregar libro
        self.btn_add_book = QPushButton("➕ Agregar Libro PDF")
        self.btn_add_book.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                margin: 5px 0px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_add_book.clicked.connect(self.on_add_book)
        layout.addWidget(self.btn_add_book)
        
        # Botón consultar IA
        self.btn_ask_ai = QPushButton("🤖 Consultar IA")
        self.btn_ask_ai.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                margin: 5px 0px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        layout.addWidget(self.btn_ask_ai)
        
        # Botón configuración
        self.btn_settings = QPushButton("⚙️ Configuración")
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                margin: 5px 0px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_settings)
        
        layout.addStretch()
        
        return panel
        
    def create_info_panel(self):
        """Crear panel de información"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Título del panel
        title = QLabel("Información del Sistema")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Estadísticas
        stats_group = QGroupBox("📊 Estadísticas")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_group)
        
        stats_info = QLabel(
            "• Libros cargados: 0\n"
            "• Vectores generados: 0\n"
            "• Consultas realizadas: 0\n"
            "• Última actividad: Nunca"
        )
        stats_info.setStyleSheet("font-size: 13px; color: #2c3e50;")
        stats_layout.addWidget(stats_info)
        
        layout.addWidget(stats_group)
        
        # Estado del sistema
        status_group = QGroupBox("🔧 Estado del Sistema")
        status_group.setStyleSheet(stats_group.styleSheet())
        
        status_layout = QVBoxLayout(status_group)
        
        status_info = QLabel(
            "• Base de datos: ✅ Conectada\n"
            "• Servicio IA: 🔄 Disponible\n"
            "• Almacenamiento: 💾 0 MB usado\n"
            "• Versión: v1.0.0"
        )
        status_info.setStyleSheet("font-size: 13px; color: #2c3e50;")
        status_layout.addWidget(status_info)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        return panel
        
    def on_add_book(self):
        """Manejador para agregar libro"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar libro PDF", 
            "", 
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            QMessageBox.information(
                self, 
                "Libro seleccionado", 
                f"Has seleccionado: {file_path}\n\n(Esta funcionalidad se implementará completamente después)"
            )