import sys
import os
# Agregar raíz del proyecto al path para los imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
                             QTextEdit, QLabel, QFrame, QGroupBox, QProgressBar,
                             QFileDialog, QMessageBox, QSplitter, QWidget, QLineEdit,
                             QDialog, QFormLayout, QDialogButtonBox, QListWidgetItem,
                             QComboBox, QScrollArea, QSizePolicy, QSpacerItem, QInputDialog,
                             QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from typing import List, Dict, Tuple
from datetime import datetime
import threading
import numpy as np

# Importar los módulos que creamos
from database.db_manager import DatabaseManager
from processing.pdf_processor import PDFProcessor
from ai.query_processor import QueryProcessor
from config.config_manager import config_manager
from views.apps.base_app import BaseApp

class ProcesarLibroThread(QThread):
    """Hilo para procesar libros en segundo plano"""
    progreso = pyqtSignal(int)
    mensaje = pyqtSignal(str)
    terminado = pyqtSignal(bool, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.db_manager = DatabaseManager()
        self.pdf_processor = PDFProcessor()

    def run(self):
        try:
            self.mensaje.emit("📖 Extrayendo texto del PDF...")
            self.progreso.emit(10)
            
            # Extraer texto y fragmentos
            fragmentos, total_paginas = self.pdf_processor.extraer_texto_pdf(self.file_path)
            
            if not fragmentos:
                self.terminado.emit(False, "No se pudo extraer texto del PDF o el PDF está vacío")
                return
            
            self.mensaje.emit(f"🔢 Procesando {len(fragmentos)} fragmentos...")
            self.progreso.emit(40)
            
            # Crear entrada en base de datos
            titulo = os.path.basename(self.file_path).replace('.pdf', '').replace('_', ' ')
            libro_id = self.db_manager.agregar_libro(
                titulo=titulo,
                total_paginas=total_paginas
            )
            
            self.mensaje.emit("🧮 Generando embeddings...")
            self.progreso.emit(60)
            
            # Generar embeddings para cada fragmento (en lotes para mejor performance)
            batch_size = config_manager.get_batch_size_embeddings()
            for i in range(0, len(fragmentos), batch_size):
                batch = fragmentos[i:i + batch_size]
                textos = [frag['contenido'] for frag in batch]
                
                # Actualizar progreso
                progreso_actual = 60 + int(20 * (i / len(fragmentos)))
                self.progreso.emit(progreso_actual)
                self.mensaje.emit(f"🧮 Generando embeddings ({i + len(batch)}/{len(fragmentos)})...")
                
                # Generar embeddings en lote
                embeddings = self.pdf_processor.generar_embeddings_lote(textos)
                
                # Asignar embeddings a los fragmentos
                for j, embedding in enumerate(embeddings):
                    if embedding:
                        batch[j]['embedding'] = embedding
            
            self.progreso.emit(80)
            
            # Guardar fragmentos en base de datos
            self.db_manager.agregar_fragmentos(libro_id, fragmentos)
            
            # ¿Eliminar PDF original?
            if not config_manager.get("almacenamiento", "conservar_pdfs", False):
                try:
                    os.remove(self.file_path)
                    mensaje_final = f"Libro '{titulo}' procesado y PDF eliminado"
                except:
                    mensaje_final = f"Libro '{titulo}' procesado (no se pudo eliminar PDF)"
            else:
                mensaje_final = f"Libro '{titulo}' procesado exitosamente"
            
            self.progreso.emit(100)
            self.terminado.emit(True, mensaje_final)
            
        except Exception as e:
            self.terminado.emit(False, f"Error procesando libro: {str(e)}")

class DialogoProgreso(QDialog):
    """Diálogo para mostrar progreso de procesamiento"""
    def __init__(self, parent=None, file_path=""):
        super().__init__(parent)
        self.setWindowTitle("Procesando Libro")
        self.setModal(True)
        self.resize(450, 200)
        self.setup_ui(file_path)
        
    def setup_ui(self, file_path):
        layout = QVBoxLayout(self)
        
        # Información del archivo
        label_archivo = QLabel(f"Procesando: {os.path.basename(file_path)}")
        label_archivo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        layout.addWidget(label_archivo)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Mensaje de estado
        self.label_mensaje = QLabel("Iniciando procesamiento...")
        self.label_mensaje.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.label_mensaje)
        
        # Botón cancelar
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_cancelar.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancelar)

class DialogoSeleccionLibros(QDialog):
    """Diálogo para seleccionar libros específicos para consulta"""
    def __init__(self, parent=None, libros=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Libros para Consulta")
        self.resize(500, 400)
        self.libros = libros or []
        self.libros_seleccionados = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instrucciones
        instrucciones = QLabel("Selecciona los libros que quieres incluir en la consulta:")
        instrucciones.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(instrucciones)
        
        # Lista de libros con checkboxes
        self.lista_libros = QListWidget()
        self.lista_libros.setSelectionMode(QListWidget.MultiSelection)
        
        for libro in self.libros:
            item = QListWidgetItem(f"{libro['titulo']} - {libro['autor'] or 'Sin autor'}")
            item.setData(Qt.UserRole, libro['id'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lista_libros.addItem(item)
        
        layout.addWidget(self.lista_libros)
        
        # Controles de selección rápida
        btn_layout = QHBoxLayout()
        btn_todos = QPushButton("Seleccionar Todos")
        btn_ninguno = QPushButton("Deseleccionar Todos")
        btn_invertir = QPushButton("Invertir Selección")
        
        btn_todos.clicked.connect(self.seleccionar_todos)
        btn_ninguno.clicked.connect(self.deseleccionar_todos)
        btn_invertir.clicked.connect(self.invertir_seleccion)
        
        btn_layout.addWidget(btn_todos)
        btn_layout.addWidget(btn_ninguno)
        btn_layout.addWidget(btn_invertir)
        layout.addLayout(btn_layout)
        
        # Botones de acción
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.aceptar_seleccion)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def seleccionar_todos(self):
        for i in range(self.lista_libros.count()):
            item = self.lista_libros.item(i)
            item.setCheckState(Qt.Checked)
            
    def deseleccionar_todos(self):
        for i in range(self.lista_libros.count()):
            item = self.lista_libros.item(i)
            item.setCheckState(Qt.Unchecked)
            
    def invertir_seleccion(self):
        for i in range(self.lista_libros.count()):
            item = self.lista_libros.item(i)
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
                
    def aceptar_seleccion(self):
        self.libros_seleccionados = []
        for i in range(self.lista_libros.count()):
            item = self.lista_libros.item(i)
            if item.checkState() == Qt.Checked:
                libro_id = item.data(Qt.UserRole)
                titulo = item.text().split(' - ')[0]
                self.libros_seleccionados.append({'id': libro_id, 'titulo': titulo})
        self.accept()

class ConsultaThread(QThread):
    """Hilo seguro para procesar consultas IA"""
    respuesta_lista = pyqtSignal(str)
    habilitar_boton = pyqtSignal()
    error_ocurrido = pyqtSignal(str)
    
    def __init__(self, pregunta, db_manager, query_processor, libros_filtrados=None):
        super().__init__()
        self.pregunta = pregunta
        self.db_manager = db_manager
        self.query_processor = query_processor
        self.libros_filtrados = libros_filtrados  # Lista de IDs de libros específicos
    
    def run(self):
        """Ejecutar consulta en el hilo secundario"""
        try:
            # Obtener fragmentos según el filtro
            if self.libros_filtrados:
                # Buscar solo en libros específicos
                todos_fragmentos = self.db_manager.obtener_fragmentos_por_libros(self.libros_filtrados)
            else:
                # Buscar en todos los libros (comportamiento original)
                todos_fragmentos = self.db_manager.obtener_todos_fragmentos()
            
            if not todos_fragmentos:
                if self.libros_filtrados:
                    self.respuesta_lista.emit("No hay fragmentos disponibles en los libros seleccionados.")
                else:
                    self.respuesta_lista.emit("No hay fragmentos de texto disponibles para buscar. Asegúrate de haber procesado libros correctamente.")
                self.habilitar_boton.emit()
                return
            
            # Encontrar fragmentos relevantes
            fragmentos_relevantes, libros_referenciados = self.query_processor.encontrar_fragmentos_relevantes(
                self.pregunta, todos_fragmentos
            )
            
            # Generar respuesta
            respuesta = self.query_processor.generar_respuesta(
                self.pregunta, fragmentos_relevantes, libros_referenciados
            )
            
            # Guardar consulta en base de datos
            self.db_manager.guardar_consulta(
                pregunta=self.pregunta,
                respuesta=respuesta,
                libros_referenciados=libros_referenciados,
                modelo=config_manager.get_modelo()
            )
            
            # Emitir señales para actualizar UI
            self.respuesta_lista.emit(respuesta)
            self.habilitar_boton.emit()
            
        except Exception as e:
            error_msg = f"Error procesando consulta:\n\n{str(e)}"
            self.error_ocurrido.emit(error_msg)

class BibliotecaApp(BaseApp):
    """Aplicación de gestión de biblioteca con IA - Versión Completa"""
    
    respuesta_lista = pyqtSignal(str)
    habilitar_boton = pyqtSignal()
    error_ocurrido = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        # Conectar señales
        self.respuesta_lista.connect(self.actualizar_respuesta_ui)
        self.habilitar_boton.connect(self.rehabilitar_boton_ui)
        self.error_ocurrido.connect(self.mostrar_error_consulta)
        
        # Inicializar managers
        self.db_manager = DatabaseManager()
        self.pdf_processor = PDFProcessor()
        self.query_processor = QueryProcessor()
        
        # Variables para selección de libros
        self.libros_consulta = None  # None = todos, lista = libros específicos
        self.libros_filtrados = []
        self.indice_actual = -1
        
        self.setup_ui()
        self.actualizar_estadisticas()
        self.actualizar_lista_libros()
        
    def get_title(self):
        return "Biblioteca IA"
        
    def get_icon(self):
        return "📚"
        
    def setup_ui(self):
        """Configurar la interfaz de la aplicación de biblioteca"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Título de la aplicación
        title = QLabel("📚 Biblioteca IA")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Contenedor principal con splitter para mejor distribución
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo - Libros y acciones
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Acciones principales
        actions_group = QGroupBox("Acciones")
        actions_layout = QVBoxLayout(actions_group)
        
        self.btn_add_book = QPushButton("➕ Agregar Libro PDF")
        self.btn_add_book.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                margin: 2px 0px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_add_book.clicked.connect(self.on_add_book)
        actions_layout.addWidget(self.btn_add_book)
        
         # Botón para búsqueda avanzada
        self.btn_buscar_avanzado = QPushButton("🔍 Búsqueda Avanzada")
        self.btn_buscar_avanzado.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
                margin: 2px 0px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.btn_buscar_avanzado.clicked.connect(self.mostrar_busqueda_avanzada)
        actions_layout.addWidget(self.btn_buscar_avanzado)
        
        actions_layout.addWidget(self.create_stats_panel())
        actions_layout.addStretch()
        
        left_layout.addWidget(actions_group)
        
        # Grupo de libros con herramientas de búsqueda
        libros_group = QGroupBox("Tus Libros")
        libros_layout = QVBoxLayout(libros_group)
        
        # Barra de búsqueda rápida
        search_layout = QHBoxLayout()
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("🔍 Buscar libro...")
        self.barra_busqueda.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.barra_busqueda.textChanged.connect(self.filtrar_libros)
        search_layout.addWidget(self.barra_busqueda)
        
        # ComboBox para ordenamiento
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(["Orden: A-Z", "Orden: Z-A", "Recientes", "Antiguos", "Más fragmentos"])
        self.combo_orden.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
                min-width: 100px;
            }
        """)
        self.combo_orden.currentTextChanged.connect(self.actualizar_lista_libros)
        search_layout.addWidget(self.combo_orden)
        
        libros_layout.addLayout(search_layout)
        
        # Contador de resultados
        self.contador_libros = QLabel("")
        self.contador_libros.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        libros_layout.addWidget(self.contador_libros)
        
        # Lista de libros con scroll
        self.lista_libros = QListWidget()
        self.lista_libros.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 2px;
                background-color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 5px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        self.lista_libros.itemDoubleClicked.connect(self.on_libro_doble_click)
        self.lista_libros.itemSelectionChanged.connect(self.on_libro_seleccionado)
        libros_layout.addWidget(self.lista_libros)
        
        # Controles de navegación rápida
        nav_layout = QHBoxLayout()
        
        self.btn_primero = QPushButton("⏮")
        self.btn_anterior = QPushButton("◀")
        self.btn_siguiente = QPushButton("▶")
        self.btn_ultimo = QPushButton("⏭")
        
        for btn in [self.btn_primero, self.btn_anterior, self.btn_siguiente, self.btn_ultimo]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                    font-size: 10px;
                    min-width: 30px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                }
            """)
            btn.clicked.connect(self.navegar_libros)
        
        nav_layout.addWidget(self.btn_primero)
        nav_layout.addWidget(self.btn_anterior)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_siguiente)
        nav_layout.addWidget(self.btn_ultimo)
        
        libros_layout.addLayout(nav_layout)
        
        # Información del libro seleccionado
        self.info_libro_label = QLabel("Selecciona un libro para ver detalles")
        self.info_libro_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #7f8c8d;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                margin-top: 5px;
            }
        """)
        self.info_libro_label.setWordWrap(True)
        libros_layout.addWidget(self.info_libro_label)
        
        left_layout.addWidget(libros_group)
        
        # Panel derecho - Consulta y respuesta
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de consulta
        consulta_group = QGroupBox("Consulta IA")
        consulta_layout = QVBoxLayout(consulta_group)
        
        # Selector de ámbito de búsqueda
        ambito_layout = QHBoxLayout()
        ambito_layout.addWidget(QLabel("Buscar en:"))
        
        self.combo_ambito = QComboBox()
        self.combo_ambito.addItems(["Todos los libros", "Libro actual", "Libros seleccionados..."])
        self.combo_ambito.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.combo_ambito.currentTextChanged.connect(self.cambiar_ambito_busqueda)
        ambito_layout.addWidget(self.combo_ambito)
        
        # Indicador de selección actual
        self.label_ambito_actual = QLabel("📚 Todos los libros")
        self.label_ambito_actual.setStyleSheet("font-size: 11px; color: #7f8c8d; font-style: italic;")
        ambito_layout.addWidget(self.label_ambito_actual)
        ambito_layout.addStretch()
        
        consulta_layout.addLayout(ambito_layout)
        
        # Campo de pregunta
        self.input_pregunta = QLineEdit()
        self.input_pregunta.setPlaceholderText("Escribe tu pregunta sobre los libros...")
        self.input_pregunta.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.input_pregunta.returnPressed.connect(self.on_enviar_consulta)
        consulta_layout.addWidget(self.input_pregunta)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        self.btn_enviar_consulta = QPushButton("🚀 Enviar Consulta")
        self.btn_enviar_consulta.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_enviar_consulta.clicked.connect(self.on_enviar_consulta)
        btn_layout.addWidget(self.btn_enviar_consulta)
        
        # Botón para consultas rápidas predefinidas
        self.btn_consultas_rapidas = QPushButton("💡 Consultas Rápidas")
        self.btn_consultas_rapidas.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.btn_consultas_rapidas.clicked.connect(self.mostrar_consultas_rapidas)
        btn_layout.addWidget(self.btn_consultas_rapidas)
        
        btn_layout.addStretch()
        consulta_layout.addLayout(btn_layout)
        
        # Área de respuesta
        respuesta_label = QLabel("Respuesta:")
        respuesta_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
        consulta_layout.addWidget(respuesta_label)
        
        self.texto_respuesta = QTextEdit()
        self.texto_respuesta.setPlaceholderText("La respuesta de la IA aparecerá aquí...")
        self.texto_respuesta.setReadOnly(True)
        self.texto_respuesta.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        consulta_layout.addWidget(self.texto_respuesta)
        
        right_layout.addWidget(consulta_group)
        
        # Configurar splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
    def create_stats_panel(self):
        """Crear panel de estadísticas compacto"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 11px; color: #495057;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        return panel

    def actualizar_lista_libros(self):
        """Actualizar la lista de libros con filtros y ordenamiento"""
        self.lista_libros.clear()
        
        # Obtener todos los libros
        libros = self.db_manager.obtener_libros()
        
        # Aplicar filtro de búsqueda
        texto_busqueda = self.barra_busqueda.text().lower()
        if texto_busqueda:
            self.libros_filtrados = [
                libro for libro in libros 
                if texto_busqueda in libro['titulo'].lower() or 
                   (libro['autor'] and texto_busqueda in libro['autor'].lower())
            ]
        else:
            self.libros_filtrados = libros
        
        # Aplicar ordenamiento
        orden = self.combo_orden.currentText()
        if orden == "Orden: A-Z":
            self.libros_filtrados.sort(key=lambda x: x['titulo'].lower())
        elif orden == "Orden: Z-A":
            self.libros_filtrados.sort(key=lambda x: x['titulo'].lower(), reverse=True)
        elif orden == "Recientes":
            self.libros_filtrados.sort(key=lambda x: x['fecha_procesado'] or '', reverse=True)
        elif orden == "Antiguos":
            self.libros_filtrados.sort(key=lambda x: x['fecha_procesado'] or '')
        elif orden == "Más fragmentos":
            self.libros_filtrados.sort(key=lambda x: x['total_fragmentos'], reverse=True)
        
        # Llenar la lista
        for libro in self.libros_filtrados:
            item_text = f"{libro['titulo']}"
            if libro['autor']:
                item_text += f" - {libro['autor']}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, libro['id'])
            self.lista_libros.addItem(item)
        
        # Actualizar contador
        total = len(libros)
        filtrados = len(self.libros_filtrados)
        if filtrados == total:
            self.contador_libros.setText(f"{total} libros")
        else:
            self.contador_libros.setText(f"{filtrados} de {total} libros")
        
        # Actualizar navegación
        self.actualizar_navegacion()

    def filtrar_libros(self):
        """Filtrar libros en tiempo real según la búsqueda"""
        self.actualizar_lista_libros()

    def actualizar_navegacion(self):
        """Actualizar estado de los botones de navegación"""
        total = len(self.libros_filtrados)
        seleccionados = self.lista_libros.selectedItems()
        
        if seleccionados:
            current_item = seleccionados[0]
            self.indice_actual = self.lista_libros.row(current_item)
        else:
            self.indice_actual = -1
        
        # Habilitar/deshabilitar botones
        self.btn_primero.setEnabled(total > 0 and self.indice_actual > 0)
        self.btn_anterior.setEnabled(total > 0 and self.indice_actual > 0)
        self.btn_siguiente.setEnabled(total > 0 and self.indice_actual < total - 1)
        self.btn_ultimo.setEnabled(total > 0 and self.indice_actual < total - 1)

    def navegar_libros(self):
        """Navegar entre libros usando los botones"""
        sender = self.sender()
        total = len(self.libros_filtrados)
        
        if total == 0:
            return
        
        if sender == self.btn_primero:
            nuevo_indice = 0
        elif sender == self.btn_anterior:
            nuevo_indice = max(0, self.indice_actual - 1)
        elif sender == self.btn_siguiente:
            nuevo_indice = min(total - 1, self.indice_actual + 1)
        elif sender == self.btn_ultimo:
            nuevo_indice = total - 1
        else:
            return
        
        if 0 <= nuevo_indice < total:
            self.lista_libros.setCurrentRow(nuevo_indice)
            self.lista_libros.scrollToItem(self.lista_libros.item(nuevo_indice))
            self.actualizar_ambito_automatico()

    def on_libro_doble_click(self, item):
        """Al hacer doble click en un libro"""
        libro_id = item.data(Qt.UserRole)
        self.mostrar_detalles_libro(libro_id)

    def on_libro_seleccionado(self):
        """Cuando se selecciona un libro de la lista"""
        self.actualizar_navegacion()
        
        items = self.lista_libros.selectedItems()
        if not items:
            self.info_libro_label.setText("Selecciona un libro para ver detalles")
            return
        
        libro_id = items[0].data(Qt.UserRole)
        libro = next((l for l in self.libros_filtrados if l['id'] == libro_id), None)
        
        if libro:
            info_text = (
                f"<b>{libro['titulo']}</b>\n"
                f"Autor: {libro['autor'] or 'No especificado'}\n"
                f"Páginas: {libro['total_paginas']}\n"
                f"Fragmentos: {libro['total_fragmentos']}\n"
                f"Procesado: {libro['fecha_procesado'].strftime('%d/%m/%Y') if libro['fecha_procesado'] else 'N/A'}"
            )
            self.info_libro_label.setText(info_text)
            
            # 🔄 ACTUALIZAR AUTOMÁTICAMENTE EL ÁMBITO
            self.actualizar_ambito_automatico()

    def mostrar_busqueda_avanzada(self):
        """Mostrar diálogo de búsqueda avanzada"""
        texto, ok = QInputDialog.getText(
            self, 
            "Búsqueda Avanzada", 
            "Buscar libro por título, autor o contenido:\n\n"
            "• Use * como comodín\n"
            "• Use comillas para frases exactas\n"
            "• Ejemplo: \"ciencia ficción\" *espacio*",
            text=self.barra_busqueda.text()
        )
        
        if ok and texto:
            self.barra_busqueda.setText(texto)

    def mostrar_consultas_rapidas(self):
        """Mostrar menú de consultas rápidas predefinidas"""
        consultas = [
            "¿Cuáles son los temas principales de mis libros?",
            "Resumen los conceptos más importantes",
            "¿Qué libros hablan sobre inteligencia artificial?",
            "Encuentra información sobre machine learning",
            "Compara los diferentes enfoques encontrados"
        ]
        
        consulta, ok = QInputDialog.getItem(
            self,
            "Consultas Rápidas",
            "Selecciona una consulta predefinida:",
            consultas,
            0,
            False
        )
        
        if ok and consulta:
            self.input_pregunta.setText(consulta)
            self.input_pregunta.setFocus()

    def mostrar_detalles_libro(self, libro_id):
        """Mostrar diálogo con detalles completos del libro"""
        libro = next((l for l in self.libros_filtrados if l['id'] == libro_id), None)
        if not libro:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detalles: {libro['titulo']}")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Información detallada
        info_text = f"""
        <h3>{libro['titulo']}</h3>
        <p><b>Autor:</b> {libro['autor'] or 'No especificado'}</p>
        <p><b>Total de páginas:</b> {libro['total_paginas']}</p>
        <p><b>Fragmentos generados:</b> {libro['total_fragmentos']}</p>
        <p><b>Fecha de procesamiento:</b> {libro['fecha_procesado'].strftime('%d/%m/%Y %H:%M') if libro['fecha_procesado'] else 'N/A'}</p>
        <p><b>ID del libro:</b> {libro['id']}</p>
        """
        
        label_info = QLabel(info_text)
        label_info.setWordWrap(True)
        layout.addWidget(label_info)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        btn_consultar = QPushButton("📖 Consultar este libro")
        btn_consultar.clicked.connect(lambda: self.consultar_libro_especifico(libro['titulo'], dialog))
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dialog.close)
        
        btn_layout.addWidget(btn_consultar)
        btn_layout.addWidget(btn_cerrar)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def consultar_libro_especifico(self, titulo_libro, dialog):
        """Preparar consulta específica para un libro"""
        dialog.close()
        consulta = f"sobre el libro '{titulo_libro}': "
        self.input_pregunta.setText(consulta)
        self.input_pregunta.setFocus()
        self.input_pregunta.setSelection(len(consulta), len(consulta))

    def cambiar_ambito_busqueda(self, ambito):
        """Cambiar el ámbito de búsqueda para las consultas"""
        if ambito == "Todos los libros":
            self.libros_consulta = None
            self.label_ambito_actual.setText("📚 Todos los libros")
            
        elif ambito == "Libro actual":
            items = self.lista_libros.selectedItems()
            if items:
                libro_id = items[0].data(Qt.UserRole)
                libro = next((l for l in self.libros_filtrados if l['id'] == libro_id), None)
                if libro:
                    self.libros_consulta = [libro_id]
                    self.label_ambito_actual.setText(f"📖 {libro['titulo']}")
                else:
                    QMessageBox.warning(self, "Selecciona un libro", "Por favor selecciona un libro primero.")
                    self.combo_ambito.setCurrentText("Todos los libros")
            else:
                QMessageBox.warning(self, "Selecciona un libro", "Por favor selecciona un libro primero.")
                self.combo_ambito.setCurrentText("Todos los libros")
                
        elif ambito == "Libros seleccionados...":
            self.seleccionar_libros_consulta()

    def actualizar_ambito_automatico(self):
        """Actualizar automáticamente el ámbito basado en la selección actual"""
        if self.combo_ambito.currentText() == "Libro actual":
            items = self.lista_libros.selectedItems()
            if items:
                libro_id = items[0].data(Qt.UserRole)
                libro = next((l for l in self.libros_filtrados if l['id'] == libro_id), None)
                if libro:
                    self.libros_consulta = [libro_id]
                    self.label_ambito_actual.setText(f"📖 {libro['titulo']}")
            else:
                # Si no hay libro seleccionado, cambiar a "Todos los libros"
                self.combo_ambito.setCurrentText("Todos los libros")

    def seleccionar_libros_consulta(self):
        """Abrir diálogo para seleccionar múltiples libros"""
        libros = self.db_manager.obtener_libros()
        if not libros:
            QMessageBox.warning(self, "Sin libros", "No hay libros disponibles para seleccionar.")
            self.combo_ambito.setCurrentText("Todos los libros")
            return
            
        dialog = DialogoSeleccionLibros(self, libros)
        if dialog.exec_() == QDialog.Accepted:
            if dialog.libros_seleccionados:
                self.libros_consulta = [libro['id'] for libro in dialog.libros_seleccionados]
                nombres = [libro['titulo'] for libro in dialog.libros_seleccionados]
                if len(nombres) > 2:
                    self.label_ambito_actual.setText(f"🎯 {len(nombres)} libros seleccionados")
                else:
                    self.label_ambito_actual.setText(f"🎯 {', '.join(nombres)}")
            else:
                self.combo_ambito.setCurrentText("Todos los libros")

    def on_add_book(self):
        """Manejador para agregar libro"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar libro PDF", 
            "", 
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self.mostrar_dialogo_progreso(file_path)

    def mostrar_dialogo_progreso(self, file_path):
        """Mostrar diálogo de progreso para procesar libro"""
        dialog = DialogoProgreso(self, file_path)
        
        # Crear y conectar thread
        self.procesar_thread = ProcesarLibroThread(file_path)
        self.procesar_thread.progreso.connect(dialog.progress_bar.setValue)
        self.procesar_thread.mensaje.connect(dialog.label_mensaje.setText)
        self.procesar_thread.terminado.connect(
            lambda exito, mensaje: self.on_procesamiento_terminado(exito, mensaje, dialog)
        )
        dialog.btn_cancelar.clicked.connect(self.procesar_thread.terminate)
        
        self.procesar_thread.start()
        dialog.exec_()

    def on_procesamiento_terminado(self, exito, mensaje, dialog):
        """Manejador cuando termina el procesamiento"""
        dialog.close()
        
        if exito:
            QMessageBox.information(self, "✅ Procesamiento Completado", mensaje)
            self.actualizar_estadisticas()
            self.actualizar_lista_libros()
        else:
            QMessageBox.critical(self, "❌ Error en Procesamiento", mensaje)

    def on_enviar_consulta(self):
        """Manejador para enviar consulta IA"""
        pregunta = self.input_pregunta.text().strip()
        if not pregunta:
            QMessageBox.warning(self, "Advertencia", "Por favor escribe una pregunta")
            return
        
        # Verificar que hay libros cargados
        libros = self.db_manager.obtener_libros()
        if not libros:
            QMessageBox.warning(
                self, 
                "Sin Libros", 
                "No hay libros cargados en el sistema.\n\n"
                "Por favor agrega algunos libros PDF antes de hacer consultas."
            )
            return
        
        # Verificar selección específica
        if self.libros_consulta and not any(libro['id'] in self.libros_consulta for libro in libros):
            QMessageBox.warning(
                self,
                "Libros no disponibles",
                "Algunos de los libros seleccionados ya no están disponibles."
            )
            self.combo_ambito.setCurrentText("Todos los libros")
            return
        
        # Verificar API key
        if not config_manager.get_api_key():
            QMessageBox.warning(
                self,
                "API Key Requerida",
                "Necesitas configurar tu API Key de OpenAI para usar las consultas IA.\n\n"
                "Ve a Configuración → IA y agrega tu API Key."
            )
            return
        
        # Deshabilitar botón durante el procesamiento
        self.btn_enviar_consulta.setEnabled(False)
        self.btn_enviar_consulta.setText("Procesando...")
        
        # Mostrar información del ámbito de búsqueda
        if self.libros_consulta:
            if len(self.libros_consulta) == 1:
                libro = next((l for l in libros if l['id'] == self.libros_consulta[0]), None)
                ambito_info = f"Buscando en: {libro['titulo'] if libro else 'libro seleccionado'}"
            else:
                ambito_info = f"Buscando en: {len(self.libros_consulta)} libros seleccionados"
        else:
            ambito_info = "Buscando en: todos los libros"
            
        self.texto_respuesta.setPlainText(f"🔄 {ambito_info}\n\nProcesando tu consulta...")
        
        # Crear y ejecutar thread de consulta
        self.consulta_thread = ConsultaThread(
            pregunta, 
            self.db_manager, 
            self.query_processor, 
            self.libros_consulta
        )
        self.consulta_thread.respuesta_lista.connect(self.actualizar_respuesta_ui)
        self.consulta_thread.habilitar_boton.connect(self.rehabilitar_boton_ui)
        self.consulta_thread.error_ocurrido.connect(self.mostrar_error_consulta)
        self.consulta_thread.start()

    def actualizar_respuesta_ui(self, respuesta):
        """Actualizar la respuesta en la UI (thread-safe)"""
        self.texto_respuesta.setPlainText(respuesta)

    def rehabilitar_boton_ui(self):
        """Rehabilitar el botón de consulta (thread-safe)"""
        self.btn_enviar_consulta.setText("🚀 Enviar Consulta")
        self.btn_enviar_consulta.setEnabled(True)

    def mostrar_error_consulta(self, error_msg):
        """Mostrar error en consulta (thread-safe)"""
        self.texto_respuesta.setPlainText(f"❌ {error_msg}")
        self.rehabilitar_boton_ui()

    def actualizar_estadisticas(self):
        """Actualizar las estadísticas en la UI"""
        stats = self.db_manager.obtener_estadisticas()
        
        stats_text = (
            f"📚 {stats['total_libros']} libros\n"
            f"📄 {stats['total_fragmentos']} fragmentos\n"
            f"💬 {stats['total_consultas']} consultas"
        )
        self.stats_label.setText(stats_text)