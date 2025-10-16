#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(clean_text)

def setup_environment():
    """Configurar el entorno igual que main_launcher.py"""
    # Las mismas rutas que main_launcher.py
    data_dir = Path("data")
    config_dir = Path("config") 
    resources_dir = Path("resources")
    src_dir = Path("src")
    
    # Crear directorios (igual que main_launcher.py)
    directories = [data_dir, config_dir, resources_dir]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        safe_print(f"✅ Directorio: {directory}")
    
    # Crear archivos básicos si las carpetas están vacías
    if not any(config_dir.iterdir()):
        (config_dir / "app_config.json").write_text('{"app": {"name": "Biblioteca IA"}}')
        safe_print("📝 Archivo de configuración creado")
    
    if not any(resources_dir.iterdir()):
        (resources_dir / "version.txt").write_text("v1.0.0")
        (resources_dir / "icons").mkdir(exist_ok=True)
        safe_print("📝 Recursos básicos creados")
    
    return config_dir, resources_dir, src_dir

def build_application():
    """Construir la aplicación"""
    system = platform.system().lower()
    
    safe_print(f"🔨 Construyendo aplicación para {system.upper()}...")
    safe_print(f"📁 Directorio actual: {Path('.').absolute()}")
    
    # Configurar entorno primero
    config_dir, resources_dir, src_dir = setup_environment()
    
    # Configuración PyInstaller
    args = [
        "pyinstaller",
        "--name=BibliotecaIA",
        "--onefile",
        "--windowed",
        "--console",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=openai",
        "--hidden-import=pydub", 
        "--hidden-import=config_manager",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=PyQt5.QtNetwork",
        "--clean",
        "--noconfirm",
    ]
    
    # Usar rutas absolutas para mayor seguridad
    if system == "windows":
        args.extend([
            f"--add-data={config_dir.absolute()};config",
            f"--add-data={resources_dir.absolute()};resources"
        ])
    else:
        args.extend([
            f"--add-data={config_dir.absolute()}:config",
            f"--add-data={resources_dir.absolute()}:resources"
        ])
    
    # Archivo principal
    main_file = src_dir / "main.py"
    args.append(str(main_file))
    
    safe_print(f"📁 Config: {config_dir.absolute()} (existe: {config_dir.exists()})")
    safe_print(f"📁 Resources: {resources_dir.absolute()} (existe: {resources_dir.exists()})")
    safe_print(f"📁 Main: {main_file} (existe: {main_file.exists()})")
    
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        safe_print("✅ PyInstaller encontrado")
        
        safe_print("🚀 Ejecutando PyInstaller...")
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        
        exe_name = "BibliotecaIA.exe" if system == "windows" else "BibliotecaIA"
        dist_path = Path("dist") / exe_name
        
        if dist_path.exists():
            file_size = dist_path.stat().st_size / (1024 * 1024)
            safe_print("✅ ¡Aplicación construida exitosamente!")
            safe_print(f"📦 Ejecutable: {dist_path}")
            safe_print(f"📊 Tamaño: {file_size:.2f} MB")
        else:
            safe_print("❌ No se pudo encontrar el ejecutable")
            if result.stderr:
                safe_print(f"Errores: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        safe_print(f"❌ Error: {e}")
        if e.stderr:
            safe_print(f"Detalles: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    build_application()