import os
import tempfile
import sys
import os
# Agregar raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QTextEdit, QProgressBar,
                             QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pydub import AudioSegment
from openai import OpenAI

from config_manager import config_manager
from views.apps.base_app import BaseApp

class TranscripcionWorker(QThread):
    """Hilo para procesar la transcripción sin bloquear la UI"""
    
    progress_updated = pyqtSignal(int, str)
    finished_success = pyqtSignal(str)
    finished_error = pyqtSignal(str)
    
    def __init__(self, archivo_path):
        super().__init__()
        self.archivo_path = archivo_path

    def run(self):
        try:
            # Obtener configuración desde el manager
            api_key = config_manager.get_api_key()
            modelo_whisper = config_manager.get("ia", "modelo_whisper", "whisper-1")
            segment_length_min = config_manager.get("transcripcion", "segment_length_min", 10)
            formatear_automaticamente = config_manager.get("transcripcion", "formatear_automaticamente", True)
            
            if not api_key:
                self.finished_error.emit("No se encontró API Key. Configúrala en la sección de Configuración.")
                return
            
            # CORRECCIÓN: Inicializar cliente de OpenAI correctamente
            self.client = OpenAI(api_key=api_key)
            self.segment_length_ms = segment_length_min * 60 * 1000
            
            self.progress_updated.emit(0, "Iniciando transcripción...")
            
            # Verificar archivo
            if not os.path.exists(self.archivo_path):
                self.finished_error.emit("El archivo no existe")
                return
            
            # Cargar audio
            self.progress_updated.emit(5, "Cargando archivo de audio...")
            audio = AudioSegment.from_file(self.archivo_path)
            duracion_ms = len(audio)
            
            # Crear directorio temporal
            temp_dir = tempfile.mkdtemp()
            segmentos = []
            
            # Dividir en segmentos
            self.progress_updated.emit(10, "Dividiendo archivo en segmentos...")
            for i, start in enumerate(range(0, len(audio), self.segment_length_ms)):
                segmento = audio[start:start + self.segment_length_ms]
                nombre_segmento = os.path.join(temp_dir, f"segment_{i}.mp3")
                segmento.export(nombre_segmento, format="mp3")
                segmentos.append(nombre_segmento)
            
            # Transcribir segmentos
            self.progress_updated.emit(20, f"Transcribiendo {len(segmentos)} segmentos...")
            textos = []
            
            for i, segmento in enumerate(segmentos):
                progreso = 20 + (i / len(segmentos)) * 60
                self.progress_updated.emit(int(progreso), f"Transcribiendo segmento {i+1}/{len(segmentos)}...")
                
                try:
                    with open(segmento, "rb") as f:
                        resultado = self.client.audio.transcriptions.create(
                            model=modelo_whisper,
                            file=f
                        )
                        textos.append(resultado.text)
                except Exception as e:
                    self.finished_error.emit(f"Error en transcripción del segmento {i+1}: {str(e)}")
                    return
            
            # Unir texto
            self.progress_updated.emit(85, "Uniendo transcripciones...")
            texto_completo = "\n".join(textos)
            
            # Formatear con GPT si está activado
            if formatear_automaticamente:
                self.progress_updated.emit(90, "Formateando texto con GPT...")
                texto_final = self.formatear_texto(texto_completo)
            else:
                texto_final = texto_completo
                self.progress_updated.emit(90, "Saltando formateo automático...")
            
            # Guardar archivo
            self.progress_updated.emit(95, "Guardando archivo...")
            nombre_base = os.path.basename(self.archivo_path)
            nombre_sin_ext = os.path.splitext(nombre_base)[0]
            archivo_salida = f"{nombre_sin_ext}_transcripcion.txt"
            
            with open(archivo_salida, "w", encoding="utf-8") as f:
                f.write(texto_final)
            
            # Limpiar temporales
            for segmento in segmentos:
                if os.path.exists(segmento):
                    os.remove(segmento)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
            self.progress_updated.emit(100, "¡Transcripción completada!")
            self.finished_success.emit(archivo_salida)
            
        except Exception as e:
            self.finished_error.emit(f"Error: {str(e)}")
        

    def formatear_texto(self, texto):
        """Formatear el texto usando GPT"""
        try:
            fragmentos = self.dividir_texto(texto)
            resultado_final = ""
            
            for i, frag in enumerate(fragmentos, 1):
                prompt = f"""
                Formatea este texto como una transcripción profesional:
                - Corrige ortografía y puntuación
                - Añade saltos de línea y párrafos donde corresponda
                - Mantén nombres, fechas y horas sin alterarlos
                - Mantén todo en español

                Fragmento {i} de {len(fragmentos)}:
                {frag}
                """
                
                respuesta = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                resultado_final += respuesta.choices[0].message.content + "\n\n"
            
            return resultado_final.strip()
        except Exception as e:
            # Si falla el formateo, devolver el texto original
            return f"Texto original (error en formateo: {str(e)}):\n\n{texto}"
    
    def dividir_texto(self, texto, max_chars=3000):
        """Dividir texto en fragmentos manejables"""
        lineas = texto.split("\n")
        fragmentos = []
        fragmento_actual = ""

        for linea in lineas:
            if len(fragmento_actual) + len(linea) + 1 > max_chars:
                fragmentos.append(fragmento_actual.strip())
                fragmento_actual = linea + "\n"
            else:
                fragmento_actual += linea + "\n"

        if fragmento_actual.strip():
            fragmentos.append(fragmento_actual.strip())

        return fragmentos

class TranscripcionApp(BaseApp):
    """Aplicación de Transcripción de Audio/Video - Versión actualizada"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()
        self.apply_styles()
        
    def get_title(self):
        return "Transcripción IA"
    
    def get_icon(self):
        return "🎤"
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("🎤 Transcripción de Audio/Video con IA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Información de configuración
        config_info = QLabel("🔧 Configuración: Usa la app de Configuración para establecer API Key y preferencias")
        config_info.setStyleSheet("""
            QLabel {
                background-color: #e8f4fd;
                border: 1px solid #3498db;
                border-radius: 5px;
                padding: 8px;
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        layout.addWidget(config_info)
        
        # Grupo de archivo
        file_group = QGroupBox("📁 Archivo a Transcribir")
        file_layout = QVBoxLayout(file_group)
        
        file_input_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Selecciona un archivo de audio o video...")
        file_input_layout.addWidget(self.file_input)
        
        self.browse_btn = QPushButton("Examinar")
        self.browse_btn.clicked.connect(self.seleccionar_archivo)
        file_input_layout.addWidget(self.browse_btn)
        file_layout.addLayout(file_input_layout)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        file_layout.addWidget(self.info_label)
        
        layout.addWidget(file_group)
        
        # Información de configuración actual
        config_status = self.create_config_status()
        layout.addWidget(config_status)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Etiqueta de estado
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #34495e; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.transcribe_btn = QPushButton("🎤 Iniciar Transcripción")
        self.transcribe_btn.clicked.connect(self.iniciar_transcripcion)
        button_layout.addWidget(self.transcribe_btn)
        
        self.cancel_btn = QPushButton("❌ Cancelar")
        self.cancel_btn.clicked.connect(self.cancelar_transcripcion)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Área de logs
        log_group = QGroupBox("📝 Registro de Actividad")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Espacio flexible
        layout.addStretch()
        
        # Verificar estado inicial
        self.verificar_configuracion()
    
    def create_config_status(self):
        """Crear grupo con información de configuración actual"""
        group = QGroupBox("⚙️ Configuración Actual")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #95a5a6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Obtener configuración actual
        api_key = config_manager.get_api_key()
        modelo_whisper = config_manager.get("ia", "modelo_whisper", "whisper-1")
        segment_length = config_manager.get("transcripcion", "segment_length_min", 10)
        auto_format = config_manager.get("transcripcion", "formatear_automaticamente", True)
        
        status_text = f"""
        🔑 API Key: {'✅ Configurada' if api_key else '❌ No configurada'}
        🎤 Modelo Whisper: {modelo_whisper}
        ⏱ Segmentos: {segment_length} minutos
        ✨ Formateo: {'✅ Activado' if auto_format else '❌ Desactivado'}
        """
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet("color: #2c3e50; font-size: 11px; font-family: monospace;")
        layout.addWidget(status_label)
        
        return group

    def verificar_configuracion(self):
        """Verificar si la configuración está completa"""
        api_key = config_manager.get_api_key()
        has_file = bool(self.file_input.text().strip())
        
        # CORREGIDO: Convertir a booleano explícito
        config_ok = bool(api_key) and has_file
        self.transcribe_btn.setEnabled(config_ok)
        
        if not api_key:
            self.status_label.setText("⚠️ Configura API Key en la app de Configuración")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 11px; font-weight: bold;")
        else:
            self.status_label.setText("✅ Configuración lista")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 11px;")
        
    def apply_styles(self):
        """Aplicar estilos a los componentes"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #34495e;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 4px;
            }
        """)
        
    def seleccionar_archivo(self):
        """Seleccionar archivo de audio/video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecciona un archivo de audio o video",
            "",
            "Archivos multimedia (*.mp3 *.wav *.m4a *.mp4 *.mov *.mkv *.avi);;Todos los archivos (*.*)"
        )
        
        if file_path:
            self.file_input.setText(file_path)
            self.actualizar_info_archivo(file_path)
            self.verificar_configuracion()
    
    def actualizar_info_archivo(self, file_path):
        """Actualizar información del archivo seleccionado"""
        try:
            audio = AudioSegment.from_file(file_path)
            duracion_ms = len(audio)
            minutos = duracion_ms / 1000 / 60
            tamaño = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            info_text = f"""
            📄 Archivo: {os.path.basename(file_path)}
            ⏱ Duración: {minutos:.2f} minutos
            📊 Tamaño: {tamaño:.2f} MB
            💰 Costo estimado: ${minutos * 0.006:.4f} USD
            """
            self.info_label.setText(info_text)
            
        except Exception as e:
            self.info_label.setText(f"❌ Error al cargar archivo: {str(e)}")
    
    def iniciar_transcripcion(self):
        """Iniciar proceso de transcripción"""
        api_key = config_manager.get_api_key()
        if not api_key:
            QMessageBox.warning(
                self, 
                "API Key Requerida", 
                "No se encontró API Key de OpenAI.\n\n"
                "Por favor, ve a la aplicación de Configuración y establece tu API Key en la sección de IA."
            )
            return
        
        if not self.file_input.text().strip():
            QMessageBox.warning(self, "Advertencia", "Selecciona un archivo")
            return
        
        # Configurar UI para procesamiento
        self.transcribe_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Iniciar worker (sin pasar API key - la obtiene del config_manager)
        self.worker = TranscripcionWorker(self.file_input.text())
        self.worker.progress_updated.connect(self.actualizar_progreso)
        self.worker.finished_success.connect(self.transcripcion_completada)
        self.worker.finished_error.connect(self.transcripcion_error)
        self.worker.start()
        
        self.log("🚀 Iniciando proceso de transcripción...")
        self.log(f"🔧 Usando configuración: {config_manager.get('ia', 'modelo_whisper')}")
    
    def cancelar_transcripcion(self):
        """Cancelar transcripción en curso"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.log("❌ Transcripción cancelada por el usuario")
            self.reset_ui()
    
    def actualizar_progreso(self, valor, mensaje):
        """Actualizar barra de progreso y estado"""
        self.progress_bar.setValue(valor)
        self.status_label.setText(mensaje)
        self.log(mensaje)
    
    def transcripcion_completada(self, archivo_salida):
        """Manejar transcripción completada exitosamente"""
        self.log(f"✅ Transcripción guardada en: {archivo_salida}")
        self.status_label.setText("¡Transcripción completada!")
        
        QMessageBox.information(
            self,
            "Transcripción Completada",
            f"La transcripción se ha guardado en:\n{archivo_salida}"
        )
        
        self.reset_ui()
    
    def transcripcion_error(self, mensaje_error):
        """Manejar error en la transcripción"""
        self.log(f"❌ Error: {mensaje_error}")
        self.status_label.setText("Error en la transcripción")
        
        QMessageBox.critical(
            self,
            "Error en Transcripción",
            mensaje_error
        )
        
        self.reset_ui()
    
    def reset_ui(self):
        """Restablecer UI a estado inicial"""
        self.transcribe_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.verificar_configuracion()
    
    def log(self, mensaje):
        """Agregar mensaje al registro"""
        self.log_text.append(f"• {mensaje}")
        # Auto-scroll al final
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)