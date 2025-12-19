import sys
import os
from pathlib import Path

def setup_environment():
    """Configurar entorno para ejecución empaquetada o desarrollo"""
    if getattr(sys, 'frozen', False):
        # Ejecutándose como ejecutable empaquetado
        base_dir = Path(sys._MEIPASS)
        app_dir = Path(sys.executable).parent
    else:
        # Ejecutándose desde código fuente
        # Si fue lanzado desde main_launcher.py, usa rutas relativas a la raíz
        base_dir = Path(__file__).parent  # src/
        app_dir = base_dir.parent         # raíz del proyecto
    
    # Configurar rutas - apuntar a directorios en la raíz
    data_dir = app_dir / "data"
    config_dir = app_dir / "config" 
    resources_dir = app_dir / "resources"
    
    # Crear subdirectorios necesarios
    (data_dir / "books").mkdir(parents=True, exist_ok=True)
    (data_dir / "vectors").mkdir(parents=True, exist_ok=True)
    (data_dir / "transcripciones").mkdir(parents=True, exist_ok=True)
    (resources_dir / "icons").mkdir(parents=True, exist_ok=True)
    
    return base_dir, app_dir, data_dir, config_dir, resources_dir

# Configurar entorno al inicio
BASE_DIR, APP_DIR, DATA_DIR, CONFIG_DIR, RESOURCES_DIR = setup_environment()

import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app import BibliotecaAppManager

def handle_exception(exc_type, exc_value, exc_traceback):
    """Manejador global de excepciones"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    print("Error crítico no capturado:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Mostrar mensaje de error al usuario
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Error Crítico")
    msg.setText("Ha ocurrido un error inesperado en la aplicación.")
    msg.setDetailedText(traceback.format_exc())
    msg.exec_()

def main():
    """Función principal de la aplicación"""
    # Configurar manejador de excepciones
    sys.excepthook = handle_exception
    
    # Configurar atributos de alta resolución ANTES de crear la aplicación
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    
    # Configurar propiedades de la aplicación
    app.setApplicationName("Sistema Biblioteca IA")
    app.setApplicationVersion("1.0.0")
    
    # Configurar fuente global - Aumentada para mejor legibilidad en 1080p
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    try:
        print("=" * 50)
        print("🚀 INICIANDO SISTEMA BIBLIOTECA IA")
        print("=" * 50)
        print(f"📁 Directorio de datos: {DATA_DIR}")
        print(f"📁 Directorio de configuración: {CONFIG_DIR}")
        print(f"📁 Directorio de recursos: {RESOURCES_DIR}")
        
        # Crear y configurar aplicación principal
        main_app = BibliotecaAppManager()
        
        # Mostrar ventana principal
        main_app.show()
        
        print("✅ Aplicación ejecutándose correctamente")
        print("📍 Presiona Ctrl+C para salir")
        
        # Ejecutar loop principal
        return_code = app.exec_()
        
        print("👋 Cerrando aplicación...")
        return return_code
        
    except Exception as e:
        print(f"❌ Error fatal durante la inicialización: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())