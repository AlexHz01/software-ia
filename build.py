#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path
import tiktoken

def safe_print(text):
    print(text)

def setup_environment():
    """Configurar el entorno"""
    data_dir = Path("data")
    config_dir = Path("config") 
    resources_dir = Path("resources")
    src_dir = Path("src")
    
    directories = [data_dir, config_dir, resources_dir]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        safe_print(f"Directorio: {directory}")
    
    return config_dir, resources_dir, src_dir

def build_application():
    """Construir la aplicación"""
    system = platform.system().lower()
    
    safe_print(f"Construyendo aplicación para {system.upper()}...")
    
    # Configurar entorno
    config_dir, resources_dir, src_dir = setup_environment()
    
    # PRIMERO: Forzar descarga de tiktoken
    safe_print("Descargando codificaciones tiktoken...")
    try:
        tiktoken.get_encoding("cl100k_base")
        tiktoken.get_encoding("p50k_base") 
        tiktoken.get_encoding("r50k_base")
        safe_print("Codificaciones tiktoken descargadas")
    except Exception as e:
        safe_print(f"Error descargando tiktoken: {e}")
    
    # Configuración PyInstaller
    args = [
        "pyinstaller",
        "--name=BibliotecaIA",
        "--onefile",
        "--windowed",
        # Dependencias PyQt5
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets", 
        "--hidden-import=PyQt5.QtNetwork",
        # Dependencias tiktoken (IMPORTANTE)
        "--hidden-import=tiktoken",
        "--hidden-import=tiktoken.core",
        "--hidden-import=tiktoken.registry", 
        "--hidden-import=tiktoken.load",
        "--collect-all=tiktoken",  # INCLUIR TODOS LOS ARCHIVOS
        # Otras dependencias
        "--hidden-import=openai",
        "--hidden-import=pydub",
        "--hidden-import=pydub.audio_segment",  # Agregado para pydub
        "--hidden-import=config_manager",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=sqlalchemy",
        "--hidden-import=psycopg2",
        "--clean",
        "--noconfirm",
    ]
    
    # Agregar datos
    separator = ";" if system == "windows" else ":"
    args.extend([
        f"--add-data={config_dir.absolute()}{separator}config",
        f"--add-data={resources_dir.absolute()}{separator}resources"
    ])
    
    # Archivo principal
    main_file = src_dir / "main.py"
    args.append(str(main_file))
    
    safe_print(f"Main: {main_file}")
    
    try:
        safe_print("Ejecutando PyInstaller...")
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        
        exe_name = "BibliotecaIA.exe" if system == "windows" else "BibliotecaIA"
        dist_path = Path("dist") / exe_name
        
        if dist_path.exists():
            file_size = dist_path.stat().st_size / (1024 * 1024)
            safe_print("¡Aplicación construida exitosamente!")
            safe_print(f"Ejecutable: {dist_path}")
            safe_print(f"Tamaño: {file_size:.2f} MB")
        else:
            safe_print("No se pudo encontrar el ejecutable")
            
    except subprocess.CalledProcessError as e:
        safe_print(f"Error: {e}")
        if e.stderr:
            safe_print(f"Detalles: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    build_application()