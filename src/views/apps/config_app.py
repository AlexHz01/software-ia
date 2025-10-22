import sys
import os
# Agregar raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGroupBox, QLineEdit, QCheckBox, QComboBox,
                             QSpinBox, QSlider, QFileDialog, QMessageBox,
                             QTabWidget, QWidget, QFormLayout)
from PyQt5.QtCore import Qt

from config.config_manager import config_manager
from views.apps.base_app import BaseApp

class ConfigApp(BaseApp):
    """Aplicación de configuración del sistema"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_current_config()
        
    def get_title(self):
        return "Configuración"
        
    def get_icon(self):
        return "⚙️"
        
    def setup_ui(self):
        """Configurar la interfaz de configuración con pestañas"""
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
        
        # Widget de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        
        # Crear pestañas
        self.create_general_tab()
        self.create_ai_tab()
        self.create_database_tab()
        self.create_biblioteca_tab()
        self.create_storage_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Botones de acción
        action_buttons = self.create_action_buttons()
        layout.addLayout(action_buttons)
        
        layout.addStretch()
        
    def create_general_tab(self):
        """Crear pestaña de configuración general"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("🌐 Configuración General")
        group.setStyleSheet(self.get_group_style())
        
        group_layout = QVBoxLayout(group)
        
        # Tema
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Tema de la interfaz:")
        theme_label.setFixedWidth(180)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro", "Automático"])
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        group_layout.addLayout(theme_layout)
        
        # Idioma
        language_layout = QHBoxLayout()
        language_label = QLabel("Idioma:")
        language_label.setFixedWidth(180)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Español", "English", "Português"])
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        group_layout.addLayout(language_layout)
        
        # Inicio automático
        self.auto_start_cb = QCheckBox("Iniciar aplicación al encender el sistema")
        group_layout.addWidget(self.auto_start_cb)
        
        # Mostrar notificaciones
        self.notifications_cb = QCheckBox("Mostrar notificaciones del sistema")
        group_layout.addWidget(self.notifications_cb)
        
        layout.addWidget(group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🌐 General")
        
    def create_ai_tab(self):
        """Crear pestaña de configuración de IA"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("🤖 Configuración de IA")
        group.setStyleSheet(self.get_group_style())
        
        group_layout = QVBoxLayout(group)
        
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
        group_layout.addLayout(api_layout)
        
        # Modelo
        model_layout = QHBoxLayout()
        model_label = QLabel("Modelo de chat:")
        model_label.setFixedWidth(180)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"])
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        group_layout.addLayout(model_layout)
        
        # Modelo Whisper
        whisper_layout = QHBoxLayout()
        whisper_label = QLabel("Modelo de transcripción:")
        whisper_label.setFixedWidth(180)
        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(["whisper-1"])
        whisper_layout.addWidget(whisper_label)
        whisper_layout.addWidget(self.whisper_combo)
        whisper_layout.addStretch()
        group_layout.addLayout(whisper_layout)
        
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
        group_layout.addLayout(temp_layout)
        
        # Conectar señal del slider
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        
        layout.addWidget(group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🤖 IA")
        
    def create_database_tab(self):
        """Crear pestaña de configuración de base de datos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de tipo de base de datos
        type_group = QGroupBox("🗄️ Tipo de Base de Datos")
        type_group.setStyleSheet(self.get_group_style())
        
        type_layout = QHBoxLayout(type_group)
        type_label = QLabel("Motor de base de datos:")
        type_label.setFixedWidth(180)
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["PostgreSQL", "SQLite"])
        self.db_type_combo.currentTextChanged.connect(self.on_db_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.db_type_combo)
        type_layout.addStretch()
        
        layout.addWidget(type_group)
        
        # Grupo de configuración PostgreSQL
        self.pg_group = QGroupBox("🐘 Configuración PostgreSQL")
        self.pg_group.setStyleSheet(self.get_group_style())
        
        pg_layout = QFormLayout(self.pg_group)
        
        self.pg_host_input = QLineEdit()
        self.pg_host_input.setPlaceholderText("localhost")
        pg_layout.addRow("Host:", self.pg_host_input)
        
        self.pg_port_input = QLineEdit()
        self.pg_port_input.setPlaceholderText("5432")
        pg_layout.addRow("Puerto:", self.pg_port_input)
        
        self.pg_user_input = QLineEdit()
        self.pg_user_input.setPlaceholderText("postgres")
        pg_layout.addRow("Usuario:", self.pg_user_input)
        
        self.pg_pass_input = QLineEdit()
        self.pg_pass_input.setEchoMode(QLineEdit.Password)
        self.pg_pass_input.setPlaceholderText("Contraseña")
        pg_layout.addRow("Contraseña:", self.pg_pass_input)
        
        self.pg_db_input = QLineEdit()
        self.pg_db_input.setPlaceholderText("biblioteca_ia")
        pg_layout.addRow("Base de datos:", self.pg_db_input)
        
        self.pg_schema_input = QLineEdit()
        self.pg_schema_input.setPlaceholderText("public")
        pg_layout.addRow("Schema:", self.pg_schema_input)
        
        # Pool de conexiones
        pool_layout = QHBoxLayout()
        self.pg_pool_min = QSpinBox()
        self.pg_pool_min.setRange(1, 20)
        self.pg_pool_min.setValue(1)
        pool_layout.addWidget(QLabel("Mín:"))
        pool_layout.addWidget(self.pg_pool_min)
        
        self.pg_pool_max = QSpinBox()
        self.pg_pool_max.setRange(1, 50)
        self.pg_pool_max.setValue(10)
        pool_layout.addWidget(QLabel("Máx:"))
        pool_layout.addWidget(self.pg_pool_max)
        pool_layout.addStretch()
        
        pg_layout.addRow("Pool conexiones:", pool_layout)
        
        layout.addWidget(self.pg_group)
        
        # Grupo de configuración SQLite
        self.sqlite_group = QGroupBox("💾 Configuración SQLite")
        self.sqlite_group.setStyleSheet(self.get_group_style())
        
        sqlite_layout = QVBoxLayout(self.sqlite_group)
        
        sqlite_path_layout = QHBoxLayout()
        sqlite_path_label = QLabel("Ruta de base de datos:")
        sqlite_path_label.setFixedWidth(150)
        self.sqlite_path_input = QLineEdit()
        self.sqlite_browse_btn = QPushButton("Examinar...")
        self.sqlite_browse_btn.clicked.connect(self.on_browse_sqlite_path)
        sqlite_path_layout.addWidget(sqlite_path_label)
        sqlite_path_layout.addWidget(self.sqlite_path_input)
        sqlite_path_layout.addWidget(self.sqlite_browse_btn)
        sqlite_layout.addLayout(sqlite_path_layout)
        
        self.sqlite_backup_cb = QCheckBox("Backup automático")
        sqlite_layout.addWidget(self.sqlite_backup_cb)
        
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(QLabel("Intervalo backup:"))
        self.sqlite_backup_days = QSpinBox()
        self.sqlite_backup_days.setRange(1, 30)
        self.sqlite_backup_days.setValue(7)
        self.sqlite_backup_days.setSuffix(" días")
        backup_layout.addWidget(self.sqlite_backup_days)
        backup_layout.addStretch()
        sqlite_layout.addLayout(backup_layout)
        
        layout.addWidget(self.sqlite_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🗄️ Base de Datos")
        
    def create_biblioteca_tab(self):
        """Crear pestaña de configuración de Biblioteca IA"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de procesamiento
        proc_group = QGroupBox("📄 Procesamiento de PDF")
        proc_group.setStyleSheet(self.get_group_style())
        
        proc_layout = QFormLayout(proc_group)
        
        self.fragment_size = QSpinBox()
        self.fragment_size.setRange(100, 5000)
        self.fragment_size.setValue(1000)
        self.fragment_size.setSuffix(" tokens")
        proc_layout.addRow("Tamaño fragmento:", self.fragment_size)
        
        self.fragment_overlap = QSpinBox()
        self.fragment_overlap.setRange(0, 1000)
        self.fragment_overlap.setValue(200)
        self.fragment_overlap.setSuffix(" tokens")
        proc_layout.addRow("Solapamiento:", self.fragment_overlap)
        
        self.max_fragments_page = QSpinBox()
        self.max_fragments_page.setRange(1, 50)
        self.max_fragments_page.setValue(10)
        proc_layout.addRow("Máx fragmentos/página:", self.max_fragments_page)
        
        self.min_fragment_length = QSpinBox()
        self.min_fragment_length.setRange(10, 500)
        self.min_fragment_length.setValue(50)
        self.min_fragment_length.setSuffix(" caracteres")
        proc_layout.addRow("Longitud mínima:", self.min_fragment_length)
        
        layout.addWidget(proc_group)
        
        # Grupo de embeddings
        embed_group = QGroupBox("🧮 Embeddings")
        embed_group.setStyleSheet(self.get_group_style())
        
        embed_layout = QFormLayout(embed_group)
        
        self.embedding_model = QComboBox()
        self.embedding_model.addItems(["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"])
        embed_layout.addRow("Modelo:", self.embedding_model)
        
        self.embedding_batch = QSpinBox()
        self.embedding_batch.setRange(1, 100)
        self.embedding_batch.setValue(10)
        embed_layout.addRow("Tamaño lote:", self.embedding_batch)
        
        self.embedding_timeout = QSpinBox()
        self.embedding_timeout.setRange(10, 120)
        self.embedding_timeout.setValue(30)
        self.embedding_timeout.setSuffix(" segundos")
        embed_layout.addRow("Timeout:", self.embedding_timeout)
        
        layout.addWidget(embed_group)
        
        # Grupo de consultas
        query_group = QGroupBox("💬 Consultas IA")
        query_group.setStyleSheet(self.get_group_style())
        
        query_layout = QFormLayout(query_group)
        
        self.top_k_fragments = QSpinBox()
        self.top_k_fragments.setRange(1, 20)
        self.top_k_fragments.setValue(5)
        query_layout.addRow("Fragmentos relevantes:", self.top_k_fragments)
        
        self.similarity_threshold = QSlider(Qt.Horizontal)
        self.similarity_threshold.setRange(0, 100)
        self.similarity_threshold.setValue(70)
        self.similarity_threshold_value = QLabel("0.7")
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self.similarity_threshold)
        threshold_layout.addWidget(self.similarity_threshold_value)
        query_layout.addRow("Umbral similitud:", threshold_layout)
        
        self.max_response_tokens = QSpinBox()
        self.max_response_tokens.setRange(500, 4000)
        self.max_response_tokens.setValue(1500)
        self.max_response_tokens.setSuffix(" tokens")
        query_layout.addRow("Máx tokens respuesta:", self.max_response_tokens)
        
        self.include_references = QCheckBox("Incluir referencias en respuestas")
        self.include_references.setChecked(True)
        query_layout.addRow("", self.include_references)
        
        layout.addWidget(query_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📚 Biblioteca IA")
        
    def create_storage_tab(self):
        """Crear pestaña de configuración de almacenamiento"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("💾 Almacenamiento")
        group.setStyleSheet(self.get_group_style())
        
        group_layout = QVBoxLayout(group)
        
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
        group_layout.addLayout(storage_layout)
        
        # Límite de almacenamiento
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Límite de almacenamiento:")
        limit_label.setFixedWidth(180)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(100, 5000)
        self.limit_spin.setSuffix(" MB")
        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.limit_spin)
        group_layout.addLayout(limit_layout)
        
        # Auto limpieza
        self.auto_clean_cb = QCheckBox("Eliminar archivos temporales automáticamente")
        group_layout.addWidget(self.auto_clean_cb)
        
        # Conservar PDFs
        self.keep_pdfs_cb = QCheckBox("Conservar archivos PDF originales después de procesar")
        group_layout.addWidget(self.keep_pdfs_cb)
        
        layout.addWidget(group)
        
        # Grupo de transcripción
        trans_group = QGroupBox("🎤 Configuración de Transcripción")
        trans_group.setStyleSheet(self.get_group_style())
        
        trans_layout = QVBoxLayout(trans_group)
        
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
        trans_layout.addLayout(segment_layout)
        
        # Formateo automático
        self.auto_format_cb = QCheckBox("Formatear automáticamente con GPT")
        self.auto_format_cb.setToolTip("Usar GPT para mejorar la calidad de la transcripción")
        trans_layout.addWidget(self.auto_format_cb)
        
        layout.addWidget(trans_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "💾 Almacenamiento")
        
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
        
        # Botón probar conexión BD
        self.test_db_btn = QPushButton("🧪 Probar Conexión BD")
        self.test_db_btn.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        self.test_db_btn.clicked.connect(self.on_test_db_connection)
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.test_db_btn)
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
        
        # Base de datos
        db_type = config_manager.get("database", "tipo", "sqlite")
        self.db_type_combo.setCurrentText("PostgreSQL" if db_type == "postgresql" else "SQLite")
        
        # PostgreSQL
        pg_config = config_manager.get("database", "postgresql")
        self.pg_host_input.setText(pg_config.get("host", "localhost"))
        self.pg_port_input.setText(str(pg_config.get("puerto", 5432)))
        self.pg_user_input.setText(pg_config.get("usuario", "postgres"))
        self.pg_pass_input.setText(pg_config.get("password", ""))
        self.pg_db_input.setText(pg_config.get("nombre_bd", "biblioteca_ia"))
        self.pg_schema_input.setText(pg_config.get("schema", "public"))
        self.pg_pool_min.setValue(pg_config.get("pool_min", 1))
        self.pg_pool_max.setValue(pg_config.get("pool_max", 10))
        
        # SQLite
        sqlite_config = config_manager.get("database", "sqlite")
        self.sqlite_path_input.setText(sqlite_config.get("ruta_db", "./data/biblioteca.db"))
        self.sqlite_backup_cb.setChecked(sqlite_config.get("auto_backup", True))
        self.sqlite_backup_days.setValue(sqlite_config.get("backup_interval_days", 7))
        
        # Biblioteca IA
        self.fragment_size.setValue(config_manager.get_tamano_fragmento())
        self.fragment_overlap.setValue(config_manager.get_solapamiento_fragmento())
        self.max_fragments_page.setValue(config_manager.get("biblioteca_ia", "procesamiento.max_fragmentos_por_pagina", 10))
        self.min_fragment_length.setValue(config_manager.get("biblioteca_ia", "procesamiento.min_longitud_fragmento", 50))
        
        self.embedding_model.setCurrentText(config_manager.get_modelo_embeddings())
        self.embedding_batch.setValue(config_manager.get_batch_size_embeddings())
        self.embedding_timeout.setValue(config_manager.get("biblioteca_ia", "embeddings.timeout", 30))
        
        self.top_k_fragments.setValue(config_manager.get_top_k_fragmentos())
        similarity = config_manager.get_umbral_similitud()
        self.similarity_threshold.setValue(int(similarity * 100))
        self.similarity_threshold_value.setText(f"{similarity:.1f}")
        self.max_response_tokens.setValue(config_manager.get_max_tokens_respuesta())
        self.include_references.setChecked(config_manager.get("biblioteca_ia", "consulta.incluir_referencias", True))
        
        # Almacenamiento
        self.storage_path_input.setText(config_manager.get("almacenamiento", "ruta_datos", "./data"))
        self.limit_spin.setValue(config_manager.get("almacenamiento", "limite_almacenamiento_mb", 1000))
        self.auto_clean_cb.setChecked(config_manager.get("almacenamiento", "auto_limpieza", True))
        self.keep_pdfs_cb.setChecked(config_manager.get("almacenamiento", "conservar_pdfs", False))
        
        # Transcripción
        self.segment_spin.setValue(config_manager.get("transcripcion", "segment_length_min", 10))
        self.auto_format_cb.setChecked(config_manager.get("transcripcion", "formatear_automaticamente", True))
        
        # Actualizar visibilidad de grupos de BD
        self.on_db_type_changed(self.db_type_combo.currentText())
        
    def on_db_type_changed(self, db_type):
        """Cuando cambia el tipo de base de datos"""
        is_postgres = db_type == "PostgreSQL"
        self.pg_group.setVisible(is_postgres)
        self.sqlite_group.setVisible(not is_postgres)
        
    def toggle_api_visibility(self, checked):
        """Alternar visibilidad de la API key"""
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            
    def on_temp_changed(self, value):
        """Cuando cambia el valor del slider de temperatura"""
        self.temp_value.setText(f"{value/100:.1f}")
        
    def on_similarity_threshold_changed(self, value):
        """Cuando cambia el umbral de similitud"""
        self.similarity_threshold_value.setText(f"{value/100:.1f}")
        
    def on_browse_storage(self):
        """Abrir diálogo para seleccionar ruta de almacenamiento"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar carpeta de almacenamiento",
            self.storage_path_input.text()
        )
        if path:
            self.storage_path_input.setText(path)
            
    def on_browse_sqlite_path(self):
        """Abrir diálogo para seleccionar ruta de SQLite"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Seleccionar archivo de base de datos SQLite",
            self.sqlite_path_input.text(),
            "SQLite Database (*.db *.sqlite)"
        )
        if path:
            self.sqlite_path_input.setText(path)
            
    def on_test_db_connection(self):
        """Probar conexión a la base de datos"""
        try:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            if db_manager.probar_conexion():
                QMessageBox.information(self, "Conexión Exitosa", "✅ La conexión a la base de datos fue exitosa.")
            else:
                QMessageBox.critical(self, "Error de Conexión", "❌ No se pudo conectar a la base de datos.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Error probando conexión: {str(e)}")
            
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
            
            # Base de datos
            db_type = "postgresql" if self.db_type_combo.currentText() == "PostgreSQL" else "sqlite"
            config_manager.set("database", "tipo", db_type)
            
            # PostgreSQL
            pg_config = {
                "host": self.pg_host_input.text(),
                "puerto": int(self.pg_port_input.text() or 5432),
                "usuario": self.pg_user_input.text(),
                "password": self.pg_pass_input.text(),
                "nombre_bd": self.pg_db_input.text(),
                "schema": self.pg_schema_input.text(),
                "pool_min": self.pg_pool_min.value(),
                "pool_max": self.pg_pool_max.value()
            }
            config_manager.set("database", "postgresql", pg_config)
            
            # SQLite
            sqlite_config = {
                "ruta_db": self.sqlite_path_input.text(),
                "auto_backup": self.sqlite_backup_cb.isChecked(),
                "backup_interval_days": self.sqlite_backup_days.value()
            }
            config_manager.set("database", "sqlite", sqlite_config)
            
            # Biblioteca IA
            config_manager.set("biblioteca_ia", "procesamiento.tamano_fragmento", self.fragment_size.value())
            config_manager.set("biblioteca_ia", "procesamiento.solapamiento_fragmento", self.fragment_overlap.value())
            config_manager.set("biblioteca_ia", "procesamiento.max_fragmentos_por_pagina", self.max_fragments_page.value())
            config_manager.set("biblioteca_ia", "procesamiento.min_longitud_fragmento", self.min_fragment_length.value())
            
            config_manager.set("biblioteca_ia", "embeddings.modelo", self.embedding_model.currentText())
            config_manager.set("biblioteca_ia", "embeddings.batch_size", self.embedding_batch.value())
            config_manager.set("biblioteca_ia", "embeddings.timeout", self.embedding_timeout.value())
            
            config_manager.set("biblioteca_ia", "consulta.top_k_fragmentos", self.top_k_fragments.value())
            config_manager.set("biblioteca_ia", "consulta.umbral_similitud", self.similarity_threshold.value() / 100)
            config_manager.set("biblioteca_ia", "consulta.max_tokens_respuesta", self.max_response_tokens.value())
            config_manager.set("biblioteca_ia", "consulta.incluir_referencias", self.include_references.isChecked())
            
            # Almacenamiento
            config_manager.set("almacenamiento", "ruta_datos", self.storage_path_input.text())
            config_manager.set("almacenamiento", "limite_almacenamiento_mb", self.limit_spin.value())
            config_manager.set("almacenamiento", "auto_limpieza", self.auto_clean_cb.isChecked())
            config_manager.set("almacenamiento", "conservar_pdfs", self.keep_pdfs_cb.isChecked())
            
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