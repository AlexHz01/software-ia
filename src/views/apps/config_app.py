import sys
import os
# Agregar raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGroupBox, QLineEdit, QCheckBox, QComboBox,
                             QSpinBox, QSlider, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt

from config_manager import config_manager  # ← Ahora sí lo encontrará
from views.apps.base_app import BaseApp

class ConfigApp(BaseApp):
    """Aplicación de configuración del sistema"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_current_config()  # ¡IMPORTANTE! Cargar configuración después de crear UI
        
    def get_title(self):
        return "Configuración"
        
    def get_icon(self):
        return "⚙️"
        
    def setup_ui(self):
        """Configurar la interfaz de configuración"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("⚙️ Configuración del Sistema")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title)
        
        # Grupo de configuración general
        general_group = self.create_general_settings()
        layout.addWidget(general_group)
        
        # Grupo de configuración de IA
        ai_group = self.create_ai_settings()
        layout.addWidget(ai_group)
        
        # Grupo de almacenamiento
        storage_group = self.create_storage_settings()
        layout.addWidget(storage_group)
        
        # Grupo de transcripción
        trans_group = self.create_transcripcion_settings()
        layout.addWidget(trans_group)
        
        # Botones de acción
        action_buttons = self.create_action_buttons()
        layout.addLayout(action_buttons)
        
        layout.addStretch()
        
    def create_general_settings(self):
        """Crear grupo de configuración general"""
        group = QGroupBox("🌐 Configuración General")
        group.setStyleSheet(self.get_group_style())
        
        layout = QVBoxLayout(group)
        
        # Tema
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Tema de la interfaz:")
        theme_label.setFixedWidth(180)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro", "Automático"])
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Idioma
        language_layout = QHBoxLayout()
        language_label = QLabel("Idioma:")
        language_label.setFixedWidth(180)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Español", "English", "Português"])
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        layout.addLayout(language_layout)
        
        # Inicio automático
        self.auto_start_cb = QCheckBox("Iniciar aplicación al encender el sistema")
        layout.addWidget(self.auto_start_cb)
        
        # Mostrar notificaciones
        self.notifications_cb = QCheckBox("Mostrar notificaciones del sistema")
        layout.addWidget(self.notifications_cb)
        
        return group
        
    def create_ai_settings(self):
        """Crear grupo de configuración de IA"""
        group = QGroupBox("🤖 Configuración de IA")
        group.setStyleSheet(self.get_group_style())
        
        layout = QVBoxLayout(group)
        
        # API Key con toggle de visibilidad
        api_layout = QHBoxLayout()
        api_label = QLabel("API Key de OpenAI:")
        api_label.setFixedWidth(180)
        
        api_input_layout = QVBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        
        self.show_api_cb = QCheckBox("Mostrar API Key")
        self.show_api_cb.toggled.connect(self.toggle_api_visibility)
        
        api_input_layout.addWidget(self.api_key_input)
        api_input_layout.addWidget(self.show_api_cb)
        
        api_layout.addWidget(api_label)
        api_layout.addLayout(api_input_layout)
        api_layout.addStretch()
        layout.addLayout(api_layout)
        
        # Modelo
        model_layout = QHBoxLayout()
        model_label = QLabel("Modelo de chat:")
        model_label.setFixedWidth(180)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"])
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)
        
        # Modelo Whisper
        whisper_layout = QHBoxLayout()
        whisper_label = QLabel("Modelo de transcripción:")
        whisper_label.setFixedWidth(180)
        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(["whisper-1"])
        whisper_layout.addWidget(whisper_label)
        whisper_layout.addWidget(self.whisper_combo)
        whisper_layout.addStretch()
        layout.addLayout(whisper_layout)
        
        # Temperatura
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperatura:")
        temp_label.setFixedWidth(180)
        
        temp_controls_layout = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_value = QLabel("0.7")
        self.temp_value.setFixedWidth(30)
        
        temp_controls_layout.addWidget(self.temp_slider)
        temp_controls_layout.addWidget(self.temp_value)
        temp_controls_layout.addStretch()
        
        temp_layout.addWidget(temp_label)
        temp_layout.addLayout(temp_controls_layout)
        layout.addLayout(temp_layout)
        
        # Conectar señal del slider
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        
        return group
        
    def create_storage_settings(self):
        """Crear grupo de configuración de almacenamiento"""
        group = QGroupBox("💾 Almacenamiento")
        group.setStyleSheet(self.get_group_style())
        
        layout = QVBoxLayout(group)
        
        # Ruta de almacenamiento
        storage_layout = QHBoxLayout()
        storage_label = QLabel("Ruta de archivos:")
        storage_label.setFixedWidth(180)
        self.storage_path_input = QLineEdit()
        self.browse_btn = QPushButton("Examinar...")
        self.browse_btn.clicked.connect(self.on_browse_storage)
        storage_layout.addWidget(storage_label)
        storage_layout.addWidget(self.storage_path_input)
        storage_layout.addWidget(self.browse_btn)
        layout.addLayout(storage_layout)
        
        # Límite de almacenamiento
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Límite de almacenamiento:")
        limit_label.setFixedWidth(180)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(100, 5000)
        self.limit_spin.setSuffix(" MB")
        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.limit_spin)
        layout.addLayout(limit_layout)
        
        # Auto limpieza
        self.auto_clean_cb = QCheckBox("Eliminar archivos temporales automáticamente")
        layout.addWidget(self.auto_clean_cb)
        
        return group
        
    def create_transcripcion_settings(self):
        """Crear grupo de configuración de transcripción"""
        group = QGroupBox("🎤 Configuración de Transcripción")
        group.setStyleSheet(self.get_group_style())
        
        layout = QVBoxLayout(group)
        
        # Duración de segmentos
        segment_layout = QHBoxLayout()
        segment_label = QLabel("Duración de segmentos:")
        segment_label.setFixedWidth(180)
        self.segment_spin = QSpinBox()
        self.segment_spin.setRange(1, 30)
        self.segment_spin.setSuffix(" minutos")
        self.segment_spin.setToolTip("Duración de cada segmento de audio para procesar")
        segment_layout.addWidget(segment_label)
        segment_layout.addWidget(self.segment_spin)
        layout.addLayout(segment_layout)
        
        # Formateo automático
        self.auto_format_cb = QCheckBox("Formatear automáticamente con GPT")
        self.auto_format_cb.setToolTip("Usar GPT para mejorar la calidad de la transcripción")
        layout.addWidget(self.auto_format_cb)
        
        return group
        
    def create_action_buttons(self):
        """Crear botones de acción"""
        layout = QHBoxLayout()
        
        # Botón guardar
        self.save_btn = QPushButton("💾 Guardar Configuración")
        self.save_btn.setStyleSheet(self.get_button_style("#27ae60", "#229954"))
        self.save_btn.clicked.connect(self.on_save_config)
        
        # Botón restaurar
        self.reset_btn = QPushButton("🔄 Restaurar Valores")
        self.reset_btn.setStyleSheet(self.get_button_style("#e67e22", "#d35400"))
        self.reset_btn.clicked.connect(self.on_reset_config)
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.reset_btn)
        layout.addStretch()
        
        return layout
        
    def get_group_style(self):
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
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
        """
        
    def get_button_style(self, color, hover_color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
        
    def load_current_config(self):
        """Cargar configuración actual desde el manager"""
        # General
        tema = config_manager.get("general", "tema", "claro")
        self.theme_combo.setCurrentText(tema.capitalize())
        
        idioma = config_manager.get("general", "idioma", "es")
        idioma_map = {"es": "Español", "en": "English", "pt": "Português"}
        self.language_combo.setCurrentText(idioma_map.get(idioma, "Español"))
        
        self.auto_start_cb.setChecked(config_manager.get("general", "auto_inicio", False))
        self.notifications_cb.setChecked(config_manager.get("general", "notificaciones", True))
        
        # IA
        self.api_key_input.setText(config_manager.get("ia", "api_key", ""))
        self.model_combo.setCurrentText(config_manager.get("ia", "modelo", "gpt-3.5-turbo"))
        self.whisper_combo.setCurrentText(config_manager.get("ia", "modelo_whisper", "whisper-1"))
        
        temperatura = config_manager.get("ia", "temperatura", 0.7)
        self.temp_slider.setValue(int(temperatura * 100))
        self.temp_value.setText(f"{temperatura:.1f}")
        
        # Almacenamiento
        self.storage_path_input.setText(config_manager.get("almacenamiento", "ruta_datos", "./data"))
        self.limit_spin.setValue(config_manager.get("almacenamiento", "limite_almacenamiento_mb", 1000))
        self.auto_clean_cb.setChecked(config_manager.get("almacenamiento", "auto_limpieza", True))
        
        # Transcripción
        self.segment_spin.setValue(config_manager.get("transcripcion", "segment_length_min", 10))
        self.auto_format_cb.setChecked(config_manager.get("transcripcion", "formatear_automaticamente", True))
        
    def toggle_api_visibility(self, checked):
        """Alternar visibilidad de la API key"""
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            
    def on_temp_changed(self, value):
        """Cuando cambia el valor del slider de temperatura"""
        self.temp_value.setText(f"{value/100:.1f}")
        
    def on_browse_storage(self):
        """Abrir diálogo para seleccionar ruta de almacenamiento"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar carpeta de almacenamiento",
            self.storage_path_input.text()
        )
        if path:
            self.storage_path_input.setText(path)
            
    def on_save_config(self):
        """Guardar configuración en el manager"""
        try:
            # General
            tema_map = {"Claro": "claro", "Oscuro": "oscuro", "Automático": "auto"}
            config_manager.set("general", "tema", tema_map[self.theme_combo.currentText()])
            
            idioma_map = {"Español": "es", "English": "en", "Português": "pt"}
            config_manager.set("general", "idioma", idioma_map[self.language_combo.currentText()])
            
            config_manager.set("general", "auto_inicio", self.auto_start_cb.isChecked())
            config_manager.set("general", "notificaciones", self.notifications_cb.isChecked())
            
            # IA
            config_manager.set("ia", "api_key", self.api_key_input.text())
            config_manager.set("ia", "modelo", self.model_combo.currentText())
            config_manager.set("ia", "modelo_whisper", self.whisper_combo.currentText())
            config_manager.set("ia", "temperatura", self.temp_slider.value() / 100)
            
            # Almacenamiento
            config_manager.set("almacenamiento", "ruta_datos", self.storage_path_input.text())
            config_manager.set("almacenamiento", "limite_almacenamiento_mb", self.limit_spin.value())
            config_manager.set("almacenamiento", "auto_limpieza", self.auto_clean_cb.isChecked())
            
            # Transcripción
            config_manager.set("transcripcion", "segment_length_min", self.segment_spin.value())
            config_manager.set("transcripcion", "formatear_automaticamente", self.auto_format_cb.isChecked())
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "✅ La configuración ha sido guardada correctamente.\n\n"
                "Los cambios están disponibles inmediatamente para todas las aplicaciones."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"❌ Error guardando configuración: {str(e)}"
            )
        
    def on_reset_config(self):
        """Restaurar valores por defecto"""
        reply = QMessageBox.question(
            self,
            "Restaurar Configuración",
            "¿Estás seguro de que quieres restaurar todos los valores a su estado por defecto?\n\n"
            "Se perderán todos los cambios no guardados.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            config_manager.config = config_manager.default_config.copy()
            config_manager.save_config()
            self.load_current_config()
            
            QMessageBox.information(
                self, 
                "Valores Restaurados", 
                "Todos los valores han sido restaurados a los valores por defecto."
            )