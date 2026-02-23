import sys
import os
import warnings

# Suppress specific PyQt5/Sip deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")

# Agregar raíz del proyecto al path para los imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
                             QTextEdit, QLabel, QFrame, QGroupBox, QProgressBar,
                             QFileDialog, QMessageBox, QSplitter, QWidget, QLineEdit,
                             QDialog, QFormLayout, QDialogButtonBox, QListWidgetItem,
                             QComboBox, QScrollArea, QSizePolicy, QSpacerItem, QInputDialog,
                             QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
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

# ============ CHAT WIDGETS ============

class ChatMessageWidget(QWidget):
    """Widget para mostrar un mensaje estilo chat"""
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.text = text
        self.is_user = is_user
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        
        if self.is_user:
            # Mensaje del usuario - alineado a la derecha
            layout.addStretch()
            bubble = self.create_bubble("#3498db", "#ffffff")
            layout.addWidget(bubble)
        else:
            # Mensaje de la IA - alineado a la izquierda con icono
            icon = QLabel("🤖")
            icon.setFixedSize(32, 32)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("""
                background-color: #2ecc71;
                border-radius: 16px;
                font-size: 18px;
            """)
            layout.addWidget(icon, alignment=Qt.AlignTop)
            
            bubble = self.create_bubble("#ecf0f1", "#2c3e50")
            layout.addWidget(bubble)
            layout.addStretch()
    
    def create_bubble(self, bg_color, text_color):
        """Crear la burbuja del mensaje"""
        bubble = QFrame()
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
                padding: 10px 15px;
            }}
        """)
        
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(5, 5, 5, 5)
        
        label = QLabel(self.text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet(f"""
            color: {text_color};
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        bubble_layout.addWidget(label)
        
        return bubble

class ChatInputArea(QWidget):
    """Área de entrada de mensajes estilo chat"""
    message_sent = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 15)
        
        # Contenedor del input
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 20px;
            }
            QFrame:focus-within {
                border-color: #3498db;
            }
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 5, 5, 5)
        
        # Campo de texto
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe tu pregunta aquí...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 5px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Botón de enviar
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_container)
    
    def send_message(self):
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()
    
    def set_enabled(self, enabled):
        """Habilitar/deshabilitar el área de entrada"""
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)

# ============ END CHAT WIDGETS ============

class HistoryItemWidget(QWidget):
    """Widget para mostrar un elemento del historial"""
    def __init__(self, consulta, parent=None):
        super().__init__(parent)
        self.consulta = consulta
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Pregunta o Título (prioridad al título)
        mostrar_texto = self.consulta.get('titulo')
        es_personalizado = False
        
        if not mostrar_texto:
            mostrar_texto = self.consulta['pregunta']
        else:
            es_personalizado = True
            
        if len(mostrar_texto) > 60:
            mostrar_texto = mostrar_texto[:57] + "..."
        
        # Si es personalizado, añadir un icono sutil
        prefix = "🏷️ " if es_personalizado else ""
        
        self.label_pregunta = QLabel(f"{prefix}{mostrar_texto}")
        self.label_pregunta.setStyleSheet(f"""
            font-weight: bold; 
            color: {'#2980b9' if es_personalizado else '#2c3e50'}; 
            font-size: 12px;
        """)
        self.label_pregunta.setWordWrap(True)
        layout.addWidget(self.label_pregunta)
        
        # Fecha
        fecha = self.consulta['fecha'].strftime("%d/%m/%Y %H:%M")
        self.label_fecha = QLabel(f"📅 {fecha}")
        self.label_fecha.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        layout.addWidget(self.label_fecha)
        
        # Títulos de libros (NUEVO)
        if self.consulta.get('libros_titulos'):
            titulos = ", ".join(self.consulta['libros_titulos'])
            if len(titulos) > 40:
                titulos = titulos[:37] + "..."
            self.label_libros = QLabel(f"📚 {titulos}")
            self.label_libros.setStyleSheet("color: #34495e; font-size: 11px; font-style: italic;")
            layout.addWidget(self.label_libros)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ecf0f1;")
        layout.addWidget(line)

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
            self.mensaje.emit("📖 Extrayendo texto e índice del PDF...")
            self.progreso.emit(10)
            
            # Extraer texto, fragmentos e índice
            fragmentos, total_paginas, indice = self.pdf_processor.extraer_texto_pdf(self.file_path)
            
            if not fragmentos:
                self.terminado.emit(False, "No se pudo extraer texto del PDF o el PDF está vacío")
                return
            
            self.mensaje.emit(f"🔢 Procesando {len(fragmentos)} fragmentos...")
            self.progreso.emit(40)
            
            # Crear entrada en base de datos
            titulo = os.path.basename(self.file_path).replace('.pdf', '').replace('_', ' ')
            
            # Guardar índice en metadatos
            metadata = {
                'indice': indice,
                'fecha_extraccion_indice': datetime.now().isoformat()
            }
            
            libro_id = self.db_manager.agregar_libro(
                titulo=titulo,
                total_paginas=total_paginas,
                metadata=metadata
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
            # SECCIÓN ELIMINADA POR SOLICITUD DE USUARIO
            # if not config_manager.get("almacenamiento", "conservar_pdfs", False):
            #     try:
            #         os.remove(self.file_path)
            #         mensaje_final = f"Libro '{titulo}' procesado y PDF eliminado"
            #     except:
            #         mensaje_final = f"Libro '{titulo}' procesado (no se pudo eliminar PDF)"
            # else:
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
        self.label_archivo = QLabel(f"Procesando: {os.path.basename(file_path)}")
        self.label_archivo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        layout.addWidget(self.label_archivo)
        
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

    def actualizar_info(self, file_path, index, total):
        """Actualizar información para procesamiento por lotes"""
        self.label_archivo.setText(f"Procesando archivo {index}/{total}: {os.path.basename(file_path)}")
        self.label_mensaje.setText("Iniciando...")
        self.progress_bar.setValue(0)

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
        instrucciones.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(instrucciones)
        
        # Buscador
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("🔍 Buscar libro...")
        self.busqueda.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background: white;
                margin-bottom: 5px;
            }
        """)
        self.busqueda.textChanged.connect(self.filtrar_libros)
        layout.addWidget(self.busqueda)
        
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

    def filtrar_libros(self, texto):
        """Filtrar la lista de libros"""
        texto = texto.lower()
        for i in range(self.lista_libros.count()):
            item = self.lista_libros.item(i)
            item_text = item.text().lower()
            item.setHidden(texto not in item_text)

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

class LibraryManagerDialog(QDialog):
    """Diálogo para gestión avanzada de biblioteca"""
    def __init__(self, parent=None, db_manager=None, app_instance=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Biblioteca")
        self.resize(800, 600)
        self.db_manager = db_manager
        self.app = app_instance # Referencia para callbacks de procesado
        
        self.libros_filtrados = []
        self.indice_actual = -1
        self.setup_ui()
        self.actualizar_lista_libros()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header con título y botón agregar
        header = QHBoxLayout()
        title = QLabel("📚 Tu Colección de Libros")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header.addWidget(title)
        
        header.addStretch()
        
        btn_add = QPushButton("➕ Agregar Libros")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        btn_add.clicked.connect(self.on_add_book_click)
        header.addWidget(btn_add)
        layout.addLayout(header)
        
        # Barra de herramientas (Búsqueda y Orden)
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #ecf0f1; border-radius: 6px; padding: 5px;")
        toolbar_layout = QHBoxLayout(toolbar)
        
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("🔍 Buscar por título o autor...")
        self.barra_busqueda.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 4px; padding: 6px; background: white;")
        self.barra_busqueda.textChanged.connect(self.filtrar_libros)
        toolbar_layout.addWidget(self.barra_busqueda)
        
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(["A-Z", "Z-A", "Más Recientes", "Más Antiguos", "Más Páginas"])
        self.combo_orden.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px; background: white;")
        self.combo_orden.currentTextChanged.connect(self.actualizar_lista_libros)
        toolbar_layout.addWidget(self.combo_orden)
        
        layout.addWidget(toolbar)
        
        # Contenido principal: Lista y Detalles en Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Lista de libros
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0,0,0,0)
        
        self.lista_libros = QListWidget()
        self.lista_libros.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #f0f0f0; }
            QListWidget::item:selected { background-color: #3498db; color: white; }
        """)
        self.lista_libros.itemSelectionChanged.connect(self.on_libro_seleccionado)
        list_layout.addWidget(self.lista_libros)
        
        self.lbl_contador = QLabel("0 libros")
        self.lbl_contador.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        list_layout.addWidget(self.lbl_contador)
        
        splitter.addWidget(list_container)
        
        # Panel de detalles
        self.details_panel = QFrame()
        self.details_panel.setStyleSheet("background-color: white; border: 1px solid #bdc3c7; border-radius: 4px;")
        details_layout = QVBoxLayout(self.details_panel)
        
        self.lbl_details = QLabel("Selecciona un libro para ver su información detallada.")
        self.lbl_details.setWordWrap(True)
        self.lbl_details.setAlignment(Qt.AlignTop)
        details_layout.addWidget(self.lbl_details)
        details_layout.addStretch()
        
        # Botones de acción para libro seleccionado
        buttons_layout = QHBoxLayout()
        
        # Eliminar btn_use ("Usar en Chat") - ELIMINADO POR SOLICITUD
        
        self.btn_delete = QPushButton("🗑️ Eliminar")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                color: #c0392b; 
                border: 1px solid #c0392b; 
                padding: 6px; 
                border-radius: 4px; 
                background: white;
            }
            QPushButton:hover { background-color: #fcebeb; }
            QPushButton:disabled { color: #bdc3c7; border-color: #bdc3c7; }
        """)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.eliminar_libro_seleccionado) 
        buttons_layout.addWidget(self.btn_delete)
        
        details_layout.addLayout(buttons_layout)
        
        splitter.addWidget(self.details_panel)
        splitter.setSizes([300, 500]) # Proporción inicial
        
        layout.addWidget(splitter)
        
        # Footer
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def on_add_book_click(self):
        """Manejador para agregar libros (soporte para múltiples archivos)"""
        # NO OCULTAMOS EL DIÁLOGO - Se mantiene abierto
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Seleccionar libros PDF", 
            "", 
            "PDF Files (*.pdf)"
        )
        
        if file_paths:
            if len(file_paths) == 1:
                self.mostrar_dialogo_progreso(file_paths[0])
            else:
                self.iniciar_procesamiento_lote(file_paths)

    def mostrar_dialogo_progreso(self, file_path):
        """Mostrar diálogo de progreso para procesar libro (single file)"""
        # Usamos self como padre para que sea modal sobre este diálogo
        dialog = DialogoProgreso(self, file_path)
        
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
        dialog.close()
        if exito:
            QMessageBox.information(self, "✅ Procesamiento Completado", mensaje)
            self.actualizar_lista_libros() # Actualizamos la lista local
        else:
            QMessageBox.critical(self, "❌ Error en Procesamiento", mensaje)

    # ============ PROCESAMIENTO POR LOTES (Copiado a Manager) ============
    
    def iniciar_procesamiento_lote(self, file_paths):
        self.cola_procesamiento = list(file_paths)
        self.resultados_procesamiento = []
        self.total_archivos_lote = len(file_paths)
        
        self.dialogo_progreso_lote = DialogoProgreso(self, file_paths[0])
        self.dialogo_progreso_lote.setWindowTitle("Procesando Lote de Libros")
        self.dialogo_progreso_lote.btn_cancelar.clicked.connect(self.cancelar_lote)
        
        self.procesar_siguiente_en_cola()
        self.dialogo_progreso_lote.exec_()
        
    def procesar_siguiente_en_cola(self):
        if not self.cola_procesamiento:
            self.finalizar_procesamiento_lote()
            return

        current_file = self.cola_procesamiento.pop(0)
        current_index = self.total_archivos_lote - len(self.cola_procesamiento)
        
        self.dialogo_progreso_lote.actualizar_info(
            current_file, 
            current_index, 
            self.total_archivos_lote
        )
        
        self.procesar_thread = ProcesarLibroThread(current_file)
        self.procesar_thread.progreso.connect(self.dialogo_progreso_lote.progress_bar.setValue)
        self.procesar_thread.mensaje.connect(self.dialogo_progreso_lote.label_mensaje.setText)
        self.procesar_thread.terminado.connect(
            lambda exito, mensaje: self.on_lote_step_terminado(exito, mensaje, current_file)
        )
        self.procesar_thread.start()
        
    def on_lote_step_terminado(self, exito, mensaje, file_path):
        filename = os.path.basename(file_path)
        self.resultados_procesamiento.append({
            'archivo': filename,
            'exito': exito,
            'mensaje': mensaje
        })
        QTimer.singleShot(500, self.procesar_siguiente_en_cola)
        
    def cancelar_lote(self):
        self.cola_procesamiento = [] 
        if hasattr(self, 'procesar_thread') and self.procesar_thread.isRunning():
            self.procesar_thread.terminate()
        self.dialogo_progreso_lote.close()
        
    def finalizar_procesamiento_lote(self):
        if self.dialogo_progreso_lote:
            self.dialogo_progreso_lote.close()
            
        errores = [r for r in self.resultados_procesamiento if not r['exito']]
        exitos = [r for r in self.resultados_procesamiento if r['exito']]
        
        self.actualizar_lista_libros()
        
        if not errores:
            QMessageBox.information(
                self, "✅ Lote Completado", 
                f"Se procesaron exitosamente {len(exitos)} libros."
            )
        else:
            msg = f"Se procesaron {len(exitos)} libros correctamente.\n"
            msg += f"Hubo errores en {len(errores)} archivos:\n\n"
            for err in errores:
                msg += f"• {err['archivo']}: {err['mensaje']}\n"
            QMessageBox.warning(self, "⚠️ Lote con Errores", msg)

    def actualizar_lista_libros(self):
        self.lista_libros.clear()
        # Forzar refresco desde DB para asegurar que vemos lo último
        libros = self.db_manager.obtener_libros(force_refresh=True)
        
        # Filtrado
        query = self.barra_busqueda.text().lower()
        if query:
            self.libros_filtrados = [l for l in libros if query in l['titulo'].lower() or (l['autor'] and query in l['autor'].lower())]
        else:
            self.libros_filtrados = list(libros)
            
        # Ordenamiento simple
        orden = self.combo_orden.currentText()
        if "A-Z" in orden: self.libros_filtrados.sort(key=lambda x: x['titulo'].lower())
        elif "Z-A" in orden: self.libros_filtrados.sort(key=lambda x: x['titulo'].lower(), reverse=True)
        # ... más lógica de orden si necesaria
        
        for libro in self.libros_filtrados:
            item = QListWidgetItem(f"{libro['titulo']}")
            item.setData(Qt.UserRole, libro)
            self.lista_libros.addItem(item)
            
        self.lbl_contador.setText(f"{len(self.libros_filtrados)} libros encontrados")
        
    def filtrar_libros(self):
        self.actualizar_lista_libros()
        
    def on_libro_seleccionado(self):
        items = self.lista_libros.selectedItems()
        if not items:
            self.lbl_details.setText("Selecciona un libro...")
            self.btn_delete.setEnabled(False)
            return
            
        libro = items[0].data(Qt.UserRole)
        self.btn_delete.setEnabled(True)
        
        html = f"""
        <h2>{libro['titulo']}</h2>
        <p><b>Autor:</b> {libro['autor'] or 'Desconocido'}</p>
        <p><b>Páginas:</b> {libro['total_paginas']}</p>
        <p><b>ID:</b> {libro['id']}</p>
        <p><i>Fecha procesamiento: {libro['fecha_procesado']}</i></p>
        <hr>
        <p>Contenido fragmentado en {libro['total_fragmentos']} partes.</p>
        """
        self.lbl_details.setText(html)

    def usar_libro_chat(self):
        pass # Obsoleto/Eliminado de UI
        
    def eliminar_libro_seleccionado(self):
        """Eliminar el libro seleccionado"""
        items = self.lista_libros.selectedItems()
        if not items: return
        
        libro = items[0].data(Qt.UserRole)
        titulo = libro['titulo']
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación", 
            f"¿Estás seguro de que deseas eliminar el libro '{titulo}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db_manager.eliminar_libro(libro['id']):
                QMessageBox.information(self, "Eliminado", f"El libro '{titulo}' ha sido eliminado.")
                self.actualizar_lista_libros()
                # Limpiar panel de detalles
                self.lbl_details.setText("Selecciona un libro para ver su información detallada.")
                self.btn_delete.setEnabled(False)
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el libro.")

class BibliotecaApp(BaseApp):
    """Aplicación de gestión de biblioteca con IA - Versión Completa"""
    
    respuesta_lista = pyqtSignal(str)
    habilitar_boton = pyqtSignal()
    error_ocurrido = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        # Conectar señales
        self.respuesta_lista.connect(self.actualizar_respuesta_chat)
        self.habilitar_boton.connect(self.rehabilitar_chat_input)
        self.error_ocurrido.connect(self.mostrar_error_chat)
        
        # Inicializar managers
        self.db_manager = DatabaseManager()
        self.pdf_processor = PDFProcessor()
        self.query_processor = QueryProcessor()
        
        # Variables para selección de libros
        self.libros_consulta = None  # None = todos, lista = libros específicos
        self.libros_filtrados = []
        self.indice_actual = -1
        
        # Variables para procesamiento por lotes
        self.cola_procesamiento = []
        self.resultados_procesamiento = []
        self.total_archivos_lote = 0
        self.dialogo_progreso_lote = None
        
        # Timer para debouncing de búsqueda
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        # self.search_timer.timeout.connect(self.actualizar_lista_libros) # Obsoleto
        
        self.setup_ui()
        self.actualizar_estadisticas()
        
    def get_title(self):
        return "Biblioteca IA"
        
    def get_icon(self):
        return "📚"
        
    def setup_ui(self):
        """Configurar la interfaz de la aplicación de biblioteca"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Splitter principal para separar Sidebar de Historial y Chat
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # --- PANEL IZQUIERDO: HISTORIAL ---
        self.history_panel = QFrame()
        self.history_panel.setFixedWidth(280)
        self.history_panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)
        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        history_title = QLabel("📜 Historial de Consultas")
        history_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 5px;")
        history_layout.addWidget(history_title)
        
        # Buscador de historial
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("🔍 Buscar en historial...")
        self.history_search.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12px;
                margin-bottom: 5px;
            }
        """)
        self.history_search.textChanged.connect(self.on_history_search_changed)
        history_layout.addWidget(self.history_search)
        
        # Lista de historial
        self.lista_historial = QListWidget()
        self.lista_historial.setContextMenuPolicy(Qt.CustomContextMenu) # Habilitar menú contextual
        self.lista_historial.customContextMenuRequested.connect(self.show_history_context_menu)
        self.lista_historial.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #e8f4f8;
            }
        """)
        self.lista_historial.itemClicked.connect(self.on_history_item_clicked)
        history_layout.addWidget(self.lista_historial)
        
        # Botón para limpiar historial
        self.btn_clear_history = QPushButton("🗑️ Limpiar Historial")
        self.btn_clear_history.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e74c3c;
                border: 1px solid #e74c3c;
                padding: 5px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #fdf2f2;
            }
        """)
        self.btn_clear_history.clicked.connect(self.on_clear_history)
        history_layout.addWidget(self.btn_clear_history)
        
        self.main_splitter.addWidget(self.history_panel)
        
        # --- PANEL DERECHO: CONTENIDO PRINCIPAL ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Contenedor principal con layout vertical
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 10, 0, 0)  # Margen superior para evitar superposición
        main_layout.setSpacing(0)
        
        # Panel superior - Libros (ELIMINADO - movido a diálogo)
        # self.books_widget = ... (código eliminado)
        
        # Panel inferior - Chat IA (ocupa todo el espacio)
        
        # Panel inferior - Chat IA (ocupa más espacio)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Header con selector de ámbito
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        header_layout.addWidget(QLabel("🔍 Contexto:"))
        
        self.btn_select_context = QPushButton("📚 Seleccionar libros...")
        self.btn_select_context.setCursor(Qt.PointingHandCursor)
        self.btn_select_context.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                color: #2c3e50;
                font-size: 13px;
                min-width: 150px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adadad;
            }
        """)
        self.btn_select_context.clicked.connect(self.seleccionar_libros_consulta)
        header_layout.addWidget(self.btn_select_context)
        
        self.label_ambito_actual = QLabel("📚 Todos los libros")
        self.label_ambito_actual.setStyleSheet("font-size: 11px; color: #7f8c8d; font-style: italic; margin-left: 5px;")
        header_layout.addWidget(self.label_ambito_actual)

        # --- INDICADORES DE ANÁLISIS ---
        header_layout.addSpacing(15)
        self.status_indicators = QWidget()
        status_layout = QHBoxLayout(self.status_indicators)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        self.lbl_status_guia = QLabel("✨")
        self.lbl_status_guia.setToolTip("Guía de Fuente")
        self.lbl_status_podcast = QLabel("🎧")
        self.lbl_status_podcast.setToolTip("Deep Dive (Podcast)")
        self.lbl_status_mapa = QLabel("🗺️")
        self.lbl_status_mapa.setToolTip("Mapa Mental")
        self.lbl_status_informe = QLabel("📄")
        self.lbl_status_informe.setToolTip("Informe de Estudio")
        self.lbl_status_cuestionario = QLabel("📝")
        self.lbl_status_cuestionario.setToolTip("Cuestionario")
        
        self.all_indicators = [
            self.lbl_status_guia, self.lbl_status_podcast, 
            self.lbl_status_mapa, self.lbl_status_informe, 
            self.lbl_status_cuestionario
        ]
        
        for lbl in self.all_indicators:
            lbl.setStyleSheet("font-size: 14px; color: #bdc3c7;") # Gris claro por defecto (no generado)
            status_layout.addWidget(lbl)
        
        # Botón Mágico: Notebook Studio
        self.btn_studio = QPushButton("🪄 Studio")
        self.btn_studio.setToolTip("Generar Mapa Mental, Informe o Cuestionario")
        self.btn_studio.setCursor(Qt.PointingHandCursor)
        self.btn_studio.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_studio.clicked.connect(self.show_studio_menu)
        header_layout.addWidget(self.btn_studio)
        
        header_layout.addWidget(self.status_indicators)
        self.status_indicators.hide() 
        self.btn_studio.hide()
        
        header_layout.addStretch()
        
        # Botón para abrir el Gestor de Biblioteca (NUEVO)
        btn_manager = QPushButton("📚 Gestionar Biblioteca")
        btn_manager.setToolTip("Abrir ventana de gestión de libros")
        btn_manager.setCursor(Qt.PointingHandCursor)
        btn_manager.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        btn_manager.clicked.connect(self.on_open_library_manager)
        header_layout.addWidget(btn_manager)

        header_layout.addSpacing(5)

        # Botón Nuevo Chat
        self.btn_new_chat = QPushButton("🆕 Nuevo Chat")
        self.btn_new_chat.setToolTip("Limpiar chat y resetear contexto")
        self.btn_new_chat.setCursor(Qt.PointingHandCursor)
        self.btn_new_chat.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.btn_new_chat.clicked.connect(self.on_nuevo_chat)
        header_layout.addWidget(self.btn_new_chat)

        # --- BOTONES NOTEBOOKLM ---
        header_layout.addSpacing(10)
        
        self.btn_source_guide = QPushButton("✨ Guía de Fuente")
        self.btn_source_guide.setToolTip("Generar resumen y temas clave")
        self.btn_source_guide.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #2c3e50;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f39c12; }
            QPushButton:disabled { background-color: #ecf0f1; color: #bdc3c7; }
        """)
        self.btn_source_guide.clicked.connect(self.on_generar_guia_fuente)
        header_layout.addWidget(self.btn_source_guide)

        self.btn_deep_dive = QPushButton("🎧 Deep Dive")
        self.btn_deep_dive.setToolTip("Generar guion de podcast")
        self.btn_deep_dive.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
            QPushButton:disabled { background-color: #ecf0f1; color: #bdc3c7; }
        """)
        self.btn_deep_dive.clicked.connect(self.on_generar_deep_dive)
        header_layout.addWidget(self.btn_deep_dive)
        
        # Botón para agregar libro (DIRECTO) - Mantenido pero reducido, o eliminado si preferimos todo en el gestor
        # Vamos a dejar solo el gestor para limpiar, así que eliminamos btn_add explícito aquí
        # btn_add = QPushButton("➕") ...
        
        # Botón de consultas rápidas (ELIMINADO)
        
        chat_layout.addWidget(header_frame)
        
        # Área de chat (historial de mensajes)
        self.chat_history = QListWidget()
        self.chat_history.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0px;
            }
            QListWidget::item:hover {
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self.chat_history.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.chat_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        chat_layout.addWidget(self.chat_history)
        
        # Mensaje de bienvenida
        self.add_ai_message("¡Hola! Soy tu asistente de biblioteca IA. Puedo ayudarte a encontrar información en tus libros. ¿Qué te gustaría saber?")
        
        # Área de entrada de chat
        self.chat_input = ChatInputArea()
        self.chat_input.message_sent.connect(self.on_enviar_consulta_chat)
        chat_layout.addWidget(self.chat_input)
        
        main_layout.addWidget(chat_widget)
        
        main_layout.addWidget(self.chat_input)
        
        right_layout.addWidget(main_container)
        self.main_splitter.addWidget(right_container)
        
        layout.addWidget(self.main_splitter)
        
        # Cargar historial inicial
        self.actualizar_lista_historial()
        
    def create_stats_panel(self):
        """Crear panel de estadísticas compacto"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 5px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        title = QLabel("📊 Estadísticas")
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: white;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1.6;
        """)
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        return panel

    def add_user_message(self, text):
        """Agregar mensaje del usuario al chat"""
        item = QListWidgetItem()
        widget = ChatMessageWidget(text, is_user=True)
        item.setSizeHint(widget.sizeHint())
        self.chat_history.addItem(item)
        self.chat_history.setItemWidget(item, widget)
        self.chat_history.scrollToBottom()
    
    def add_ai_message(self, text):
        """Agregar mensaje de la IA al chat"""
        item = QListWidgetItem()
        widget = ChatMessageWidget(text, is_user=False)
        item.setSizeHint(widget.sizeHint())
        self.chat_history.addItem(item)
        self.chat_history.setItemWidget(item, widget)
        self.chat_history.scrollToBottom()
    
    def add_system_message(self, text):
        """Agregar mensaje del sistema (como mensaje de IA)"""
        self.add_ai_message(f"ℹ️ {text}")
    
    def on_enviar_consulta_chat(self, pregunta):
        """Manejador para enviar consulta desde el chat"""
        # Verificar que hay libros cargados
        libros = self.db_manager.obtener_libros()
        if not libros:
            self.add_system_message("No hay libros cargados. Por favor agrega algunos libros PDF antes de hacer consultas.")
            return
        
        # Verificar selección específica
        if self.libros_consulta and not any(libro['id'] in self.libros_consulta for libro in libros):
            self.add_system_message("Algunos libros seleccionados ya no están disponibles. Buscando en todos los libros.")
            self.libros_consulta = None
            self.combo_ambito.setCurrentText("Todos los libros")
        
        # Verificar API key
        if not config_manager.get_api_key():
            self.add_system_message("API Key Requerida. Ve a Configuración → IA y agrega tu API Key.")
            return
        
        # Agregar mensaje del usuario
        self.add_user_message(pregunta)
        
        # Deshabilitar entrada durante procesamiento
        self.chat_input.set_enabled(False)
        
        # Crear y ejecutar thread de consulta
        self.consulta_thread = ConsultaThread(
            pregunta, 
            self.db_manager, 
            self.query_processor, 
            self.libros_consulta
        )
        self.consulta_thread.respuesta_lista.connect(self.actualizar_respuesta_chat)
        self.consulta_thread.habilitar_boton.connect(self.rehabilitar_chat_input)
        self.consulta_thread.habilitar_boton.connect(self.actualizar_lista_historial) # Actualizar historial
        self.consulta_thread.error_ocurrido.connect(self.mostrar_error_chat)
        self.consulta_thread.start()
    
    def actualizar_respuesta_chat(self, respuesta):
        """Actualizar con respuesta de IA en el chat"""
        self.add_ai_message(respuesta)
    
    def rehabilitar_chat_input(self):
        """Rehabilitar entrada de chat"""
        self.chat_input.set_enabled(True)
    
    def mostrar_error_chat(self, error_msg):
        """Mostrar error en el chat"""
        self.add_system_message(f"Error: {error_msg}")
        self.chat_input.set_enabled(True)

    def actualizar_lista_historial(self, busqueda=None):
        """Actualizar la lista de historial desde la BD"""
        self.lista_historial.clear()
        historial = self.db_manager.obtener_historial_consultas(busqueda=busqueda)
        
        for consulta in historial:
            item = QListWidgetItem()
            widget = HistoryItemWidget(consulta)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, consulta['id'])
            self.lista_historial.addItem(item)
            self.lista_historial.setItemWidget(item, widget)

    def on_history_search_changed(self, text):
        """Manejador para búsqueda en el historial"""
        self.actualizar_lista_historial(busqueda=text)

    def on_history_item_clicked(self, item):
        """Manejador para cuando se hace click en un item del historial"""
        consulta_id = item.data(Qt.UserRole)
        # Buscar la consulta en el historial cargado
        historial = self.db_manager.obtener_historial_consultas()
        consulta = next((c for c in historial if c['id'] == consulta_id), None)
        
        if consulta:
            # Limpiar chat y cargar esta conversación
            self.chat_history.clear()
            self.add_user_message(consulta['pregunta'])
            self.add_ai_message(consulta['respuesta'])
            
            # Si hay libros referenciados, restaurar el contexto
            if consulta['libros_referenciados']:
                self.libros_consulta = consulta['libros_referenciados']
                titulos = consulta.get('libros_titulos', [])
                if titulos:
                    if len(titulos) == 1:
                        self.label_ambito_actual.setText(f"📖 {titulos[0]}")
                    else:
                        self.label_ambito_actual.setText(f"🎯 {len(titulos)} libros (historial)")
                else:
                    self.label_ambito_actual.setText(f"🎯 {len(self.libros_consulta)} libros (historial)")
                
                self.actualizar_indicadores_analisis()
            else:
                self.libros_consulta = None
                self.label_ambito_actual.setText("📚 Todos los libros")
                self.actualizar_indicadores_analisis()

    def show_history_context_menu(self, pos):
        """Mostrar menú contextual para elementos del historial"""
        item = self.lista_historial.itemAt(pos)
        if not item:
            return
            
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        rename_action = menu.addAction("✏️ Cambiar Nombre")
        delete_action = menu.addAction("🗑️ Eliminar")
        
        # Estilizar menú
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #3498db;
                border-top: none;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 8px 25px;
                color: #2c3e50;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        action = menu.exec_(self.lista_historial.mapToGlobal(pos))
        
        if action == rename_action:
            self.rename_history_item(item)
        elif action == delete_action:
            self.delete_history_item(item)

    def rename_history_item(self, item):
        """Abrir diálogo para renombrar un elemento del historial"""
        consulta_id = item.data(Qt.UserRole)
        
        # Obtener datos actuales
        historial = self.db_manager.obtener_historial_consultas()
        consulta = next((c for c in historial if c['id'] == consulta_id), None)
        
        if not consulta:
            return
            
        from PyQt5.QtWidgets import QInputDialog
        nombre_actual = consulta.get('titulo') or ""
        
        nuevo_nombre, ok = QInputDialog.getText(
            self, "Renombrar Historial", 
            "Ingresa un nombre para esta consulta:",
            text=nombre_actual
        )
        
        if ok and nuevo_nombre:
            if self.db_manager.actualizar_titulo_consulta(consulta_id, nuevo_nombre):
                self.actualizar_lista_historial()
                self.add_system_message(f"Historial renombrado a: {nuevo_nombre}")

    def delete_history_item(self, item):
        """Eliminar un elemento específico del historial"""
        consulta_id = item.data(Qt.UserRole)
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Estás seguro de que deseas eliminar esta consulta del historial?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db_manager.eliminar_consulta(consulta_id):
                self.actualizar_lista_historial()
                self.add_system_message("Consulta eliminada del historial.")

    def on_clear_history(self):
        """Limpiar todo el historial (con confirmación)"""
        reply = QMessageBox.question(
            self, "Confirmar", "¿Estás seguro de que deseas eliminar todo el historial de consultas?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Por ahora eliminamos uno por uno o implementamos un clear_all en db_manager
            historial = self.db_manager.obtener_historial_consultas()
            for c in historial:
                self.db_manager.eliminar_consulta(c['id'])
            self.actualizar_lista_historial()
            QMessageBox.information(self, "Éxito", "Historial eliminado correctamente.")


    def on_nuevo_chat(self):
        """Limpiar el chat y resetear el contexto"""
        self.chat_history.clear()
        self.libros_consulta = None
        self.label_ambito_actual.setText("📚 Todos los libros")
        self.add_system_message("Nuevo chat iniciado. Contexto reseteado a toda la biblioteca.")
        self.actualizar_indicadores_analisis()

    def actualizar_indicadores_analisis(self):
        """Actualizar los iconos de estado de análisis según la selección"""
        # Regla de Oro: Solo mostrar si hay exactamente UN libro seleccionado
        if not self.libros_consulta or len(self.libros_consulta) != 1:
            self.status_indicators.hide()
            self.btn_studio.hide()
            # Ocultar botones avanzados de NotebookLM si hay varios o ninguno
            self.btn_source_guide.hide()
            self.btn_deep_dive.hide()
            return
        
        # Mostrar botones solo para single book selection
        self.btn_source_guide.show()
        self.btn_deep_dive.show()
        self.btn_studio.show()
        self.status_indicators.show()
        
        # Obtener libro seleccionado
        libros = self.db_manager.obtener_libros()
        libro = next((l for l in libros if l['id'] == self.libros_consulta[0]), None)
        
        if not libro:
            self.status_indicators.hide()
            return
            
        # Actualizar colores/checkmarks según lo que ya existe
        def set_status(lbl, exists, tool_tip_base):
            if exists:
                lbl.setStyleSheet("font-size: 14px; color: #f1c40f;") # Dorado/Activo
                lbl.setToolTip(f"{tool_tip_base} (Disponible)")
            else:
                lbl.setStyleSheet("font-size: 14px; color: #bdc3c7;") # Gris (No generado)
                lbl.setToolTip(f"{tool_tip_base} (No generado)")

        set_status(self.lbl_status_guia, libro.get('guia_fuente'), "Guía de Fuente")
        set_status(self.lbl_status_podcast, libro.get('guion_podcast'), "Deep Dive (Podcast)")
        set_status(self.lbl_status_mapa, libro.get('mapa_mental'), "Mapa Mental")
        set_status(self.lbl_status_informe, libro.get('informe_estudio'), "Informe de Estudio")
        set_status(self.lbl_status_cuestionario, libro.get('cuestionario'), "Cuestionario")

    def on_open_library_manager(self):
        """Abrir diálogo de gestión de biblioteca"""
        dialog = LibraryManagerDialog(self, self.db_manager, self)
        dialog.exec_()

    def show_studio_menu(self):
        """Mostrar menú con opciones avanzadas de Notebook Studio"""
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Obtener libro actual para chequear qué ya existe
        libros = self.db_manager.obtener_libros()
        libro = next((l for l in libros if l['id'] == self.libros_consulta[0]), None) if self.libros_consulta else None
        
        def get_text(base, field):
            return f"✅ {base}" if libro and libro.get(field) else base

        mapa_action = menu.addAction(get_text("🗺️ Generar Mapa Mental", "mapa_mental"))
        informe_action = menu.addAction(get_text("📄 Generar Informe Pro", "informe_estudio"))
        quiz_action = menu.addAction(get_text("📝 Generar Cuestionario", "cuestionario"))
        
        # Estilo Studio (Púrpura)
        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #9b59b6; border-radius: 4px; }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background-color: #9b59b6; color: white; }
        """)
        
        action = menu.exec_(self.btn_studio.mapToGlobal(QPoint(0, self.btn_studio.height())))
        
        if action == mapa_action:
            self.generar_studio_output("mapa")
        elif action == informe_action:
            self.generar_studio_output("informe")
        elif action == quiz_action:
            self.generar_studio_output("cuestionario")

    def generar_studio_output(self, tipo):
        """Flujo de generación para Notebook Studio"""
        if not self.libros_consulta or len(self.libros_consulta) != 1:
            return
            
        libro_id = self.libros_consulta[0]
        libros = self.db_manager.obtener_libros()
        libro = next((l for l in libros if l['id'] == libro_id), None)
        
        # Verificar caché primero
        field_map = {"mapa": "mapa_mental", "informe": "informe_estudio", "cuestionario": "cuestionario"}
        emoji_map = {"mapa": "🗺️", "informe": "📄", "cuestionario": "📝"}
        title_map = {"mapa": "Mapa Mental", "informe": "Informe Profesional", "cuestionario": "Cuestionario de Autoevaluación"}
        
        field = field_map[tipo]
        if libro and libro.get(field):
            content = libro[field]
            self.add_system_message(f"Recuperando {title_map[tipo]} guardado...")
            if tipo == "mapa":
                # Envolver Mermaid para la UI
                self.add_ai_message(f"### {emoji_map[tipo]} {title_map[tipo]} (Mermaid)\n\n```mermaid\n{content}\n```")
            else:
                self.add_ai_message(f"### {emoji_map[tipo]} {title_map[tipo]}\n\n{content}")
            return

        self.add_system_message(f"🪄 Studio: Generando {title_map[tipo]}... (puede tardar unos segundos)")
        self.chat_input.set_enabled(False)
        
        def run():
            try:
                fragmentos = self.db_manager.obtener_fragmentos_por_libros([libro_id])
                
                if tipo == "mapa":
                    output = self.query_processor.generar_mapa_mental(fragmentos)
                elif tipo == "informe":
                    output = self.query_processor.generar_informe(fragmentos)
                else:
                    output = self.query_processor.generar_cuestionario(fragmentos)
                
                # Guardar en BD
                self.db_manager.actualizar_studio_libro(libro_id, tipo, output)
                
                header = f"### {emoji_map[tipo]} {title_map[tipo]}"
                if tipo == "mapa":
                    # Limpiar Mermaid si viene con bloques de código
                    output = output.replace("```mermaid", "").replace("```", "").strip()
                    self.respuesta_lista.emit(f"{header}\n\n```mermaid\n{output}\n```")
                else:
                    self.respuesta_lista.emit(f"{header}\n\n{output}")
                    
                # Forzar actualización de indicadores
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.actualizar_indicadores_analisis())
                
            except Exception as e:
                self.error_ocurrido.emit(str(e))
            finally:
                self.habilitar_boton.emit()

        threading.Thread(target=run).start()

    def on_generar_guia_fuente(self):
        """Generar y mostrar la Guía de Fuente (Solo Single Book)"""
        if not self.libros_consulta or len(self.libros_consulta) != 1:
            QMessageBox.warning(self, "Atención", "Selecciona exactamente un libro para la Guía de Fuente.")
            return

        libros = self.db_manager.obtener_libros()

        libros_a_procesar = [l for l in libros if l['id'] in self.libros_consulta]
        
        # --- LÓGICA DE CACHÉ / PERSISTENCIA ---
        if len(libros_a_procesar) == 1:
            libro = libros_a_procesar[0]
            if libro.get('guia_fuente'):
                self.add_system_message(f"Recuperando guía guardada para: {libro['titulo']}")
                self.add_ai_message(f"### ✨ Guía de Fuente (Guardada)\n\n{libro['guia_fuente']}")
                return

        self.add_system_message(f"Generando Guía de Fuente para {len(libros_a_procesar)} libro(s)...")
        self.chat_input.set_enabled(False)
        
        def run():
            try:
                if self.libros_consulta:
                    fragmentos = self.db_manager.obtener_fragmentos_por_libros(self.libros_consulta)
                else:
                    fragmentos = self.db_manager.obtener_todos_fragmentos()
                
                guia = self.query_processor.generar_guia_fuente(libros_a_procesar, fragmentos)
                
                # Guardar si es un solo libro
                if len(libros_a_procesar) == 1:
                    self.db_manager.actualizar_guia_fuente(libros_a_procesar[0]['id'], guia)
                
                self.respuesta_lista.emit(f"### ✨ Guía de Fuente\n\n{guia}")
            except Exception as e:
                self.error_ocurrido.emit(str(e))
            finally:
                self.habilitar_boton.emit()

        threading.Thread(target=run).start()

    def on_generar_deep_dive(self):
        """Generar un guion de podcast (Deep Dive) - Solo Single Book"""
        if not self.libros_consulta or len(self.libros_consulta) != 1:
            QMessageBox.warning(self, "Atención", "Selecciona exactamente un libro para generar un Deep Dive.")
            return

        libros = self.db_manager.obtener_libros()

        libros_a_procesar = [l for l in libros if l['id'] in self.libros_consulta]

        # --- CACHÉ PARA DEEP DIVE (Solo si es 1 libro) ---
        if len(libros_a_procesar) == 1:
            libro = libros_a_procesar[0]
            if libro.get('guion_podcast'):
                self.add_system_message(f"Recuperando Deep Dive guardado para: {libro['titulo']}")
                self.add_ai_message(f"### 🎧 Deep Dive (Guardado)\n\n{libro['guion_podcast']}")
                return

        self.add_system_message("Sumergiéndome en los documentos para generar un Deep Dive (Podcast)...")
        self.chat_input.set_enabled(False)

        def run():
            try:
                if self.libros_consulta:
                    fragmentos = self.db_manager.obtener_fragmentos_por_libros(self.libros_consulta)
                else:
                    fragmentos = self.db_manager.obtener_todos_fragmentos()
                
                guion = self.query_processor.generar_guion_podcast(fragmentos)

                # Guardar si es un solo libro
                if self.libros_consulta and len(self.libros_consulta) == 1:
                    self.db_manager.actualizar_guion_podcast(self.libros_consulta[0], guion)

                self.respuesta_lista.emit(f"### 🎧 Deep Dive (Podcast Script)\n\n{guion}")
            except Exception as e:
                self.error_ocurrido.emit(str(e))
            finally:
                self.habilitar_boton.emit()

        threading.Thread(target=run).start()

    def set_current_book_context(self, book_id, title):
        """Establecer un libro específico como contexto del chat desde el Manager"""
        self.libros_consulta = [book_id]
        self.label_ambito_actual.setText(f"📖 {title}")
        self.set_info_status(f"Contexto: {title}")
        self.actualizar_indicadores_analisis()

    def set_info_status(self, text):
        # Helper simple para mostrar estado
        pass

    def cambiar_ambito_busqueda(self, ambito):
        """Cambiar el ámbito de búsqueda para las consultas"""
        if ambito == "Todos los libros":
            self.libros_consulta = None
            self.label_ambito_actual.setText("📚 Todos los libros")
            self.set_info_status("Búsqueda en toda la biblioteca")
            self.actualizar_indicadores_analisis()
            
        elif ambito == "Libros seleccionados...":
            self.seleccionar_libros_consulta()
            
        elif ambito == "Libro actual":
            QMessageBox.information(self, "Info", "Usa 'Gestionar Biblioteca' o 'Seleccionar libros' para filtrar.")

    def actualizar_ambito_automatico(self):
        # Desactivado - ya no hay lista seleccionable en main UI
        pass
    
    # ===================================================

    def seleccionar_libros_consulta(self):
        """Abrir diálogo para seleccionar múltiples libros"""
        # Forzar refresco para ver libros acabados de agregar
        libros = self.db_manager.obtener_libros(force_refresh=True)
        if not libros:
            QMessageBox.warning(self, "Sin libros", "No hay libros disponibles para seleccionar.")
            # self.combo_ambito.setCurrentText("Todos los libros") # ELIMINADO
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
                self.actualizar_indicadores_analisis()
            else:
                self.label_ambito_actual.setText("📚 Todos los libros")
                self.libros_consulta = None
                self.actualizar_indicadores_analisis()
                
    # ... (Resto de on_add_book, etc) - ELIMINADO: Movido a LibraryManagerDialog
    # def on_add_book(self): ...
    # def mostrar_dialogo_progreso(self): ...

    def on_procesamiento_terminado(self, exito, mensaje, dialog):
        """Manejador cuando termina el procesamiento (single file)"""
        dialog.close()
        
        if exito:
            QMessageBox.information(self, "✅ Procesamiento Completado", mensaje)
            self.actualizar_estadisticas()
            # self.actualizar_lista_libros() # ELIMINADO - Ya no actualizamos lista en main UI
        else:
            QMessageBox.critical(self, "❌ Error en Procesamiento", mensaje)

    # Los métodos de procesamiento por lote también han sido movidos al Manager

    # ... (on_enviar_consulta, etc)
    def actualizar_estadisticas(self):
        """Actualizar las estadísticas en la UI"""
        # Panel de estadísticas removido - método mantenido para compatibilidad
        pass

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    # Configurar aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Biblioteca IA (Standalone)")
    
    # Configurar fuente con escalado básico para standalone
    screen = app.primaryScreen()
    height = screen.geometry().height()
    
    scale = 1.25
    if height >= 2100: scale = 2.4
    elif height >= 1400: scale = 1.8
        
    font = QFont("Segoe UI", int(10 * scale))
    app.setFont(font)
    
    try:
        # Instanciar y mostrar app
        window = BibliotecaApp()
        window.resize(1000, 700)
        window.show()
        
        print("✅ BibliotecaApp iniciada en modo standalone")
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Error al iniciar: {e}")
        import traceback
        traceback.print_exc()