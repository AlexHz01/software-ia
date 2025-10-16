#!/usr/bin/env python3
"""
Lanzador principal - ejecutar este archivo para iniciar la aplicación desde la raíz
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Configurar entorno desde la raíz del proyecto"""
    # Agregar src al path para que Python encuentre los módulos
    SRC_DIR = Path(__file__).parent / "src"
    sys.path.insert(0, str(SRC_DIR))
    
    # Configurar rutas de datos
    data_dir = Path(__file__).parent / "data"
    config_dir = Path(__file__).parent / "config"
    resources_dir = Path(__file__).parent / "resources"
    
    # Crear directorios si no existen
    directories = [data_dir, config_dir, resources_dir]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Iniciando Biblioteca IA")
    print(f"📁 Directorio raíz: {Path(__file__).parent}")
    print(f"📁 Directorio src: {SRC_DIR}")
    print(f"📁 Datos: {data_dir}")
    print(f"📁 Configuración: {config_dir}")
    
    return SRC_DIR, data_dir, config_dir, resources_dir

if __name__ == "__main__":
    try:
        # Configurar entorno
        SRC_DIR, DATA_DIR, CONFIG_DIR, RESOURCES_DIR = setup_environment()
        
        # Cambiar al directorio src para ejecución
        os.chdir(SRC_DIR)
        
        # Importar y ejecutar main desde src
        from main import main
        main()
        
    except Exception as e:
        print(f"❌ Error fatal al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")