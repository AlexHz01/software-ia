#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path

def safe_print(text):
    """Imprimir texto de forma segura evitando errores de Unicode"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Si falla con emojis, usar texto simple
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(clean_text)

def build_application():
    """Construir la aplicación para diferentes plataformas"""
    system = platform.system().lower()
    
    safe_print("🔨 Construyendo aplicación para " + system.upper() + "...")
    safe_print("📁 Directorio actual: " + str(Path('.').absolute()))
    
    # Configuración base común
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
        "--clean",
        "--noconfirm",
    ]
    
    # Agregar icono si existe
    icon_path = "resources/icon.ico"
    if Path(icon_path).exists():
        args.append(f"--icon={icon_path}")
        safe_print("✅ Usando icono personalizado")
    else:
        safe_print("⚠️  No se encontró icono, usando predeterminado")
    
    # Agregar datos según plataforma
    if system == "windows":
        args.extend([
            "--add-data=config;config",
            "--add-data=resources;resources"
        ])
    else:  # Linux
        args.extend([
            "--add-data=config:config",
            "--add-data=resources:resources"
        ])
    
    # Archivo principal
    args.append("src/main.py")
    
    try:
        # Verificar que PyInstaller está instalado
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        safe_print("✅ PyInstaller encontrado")
        
        # Ejecutar PyInstaller
        safe_print("🚀 Ejecutando PyInstaller...")
        result = subprocess.run(args, check=True, capture_output=True, text=True, shell=(system == "windows"))
        
        # Verificar resultado
        exe_name = "BibliotecaIA.exe" if system == "windows" else "BibliotecaIA"
        dist_path = Path("dist") / exe_name
        
        if dist_path.exists():
            file_size = dist_path.stat().st_size / (1024 * 1024)  # MB
            safe_print("✅ ¡Aplicación construida exitosamente!")
            safe_print("📦 Ejecutable: " + str(dist_path.absolute()))
            safe_print(f"📊 Tamaño: {file_size:.2f} MB")
            
            # Listar contenido de dist/
            safe_print("📁 Contenido de dist/:")
            for item in Path("dist").iterdir():
                safe_print("   - " + item.name)
                
        else:
            safe_print("❌ No se pudo encontrar el ejecutable")
            if result.stderr:
                safe_print("Errores:")
                safe_print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        safe_print("❌ Error durante la construcción: " + str(e))
        if e.stderr:
            safe_print("Detalles: " + e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        safe_print("❌ PyInstaller no está instalado")
        # Intentar instalar PyInstaller
        try:
            safe_print("🔄 Instalando PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            safe_print("✅ PyInstaller instalado, reintentando construcción...")
            # Reintentar construcción
            result = subprocess.run(args, check=True, capture_output=True, text=True, shell=(system == "windows"))
        except:
            safe_print("❌ No se pudo instalar PyInstaller automáticamente")
            sys.exit(1)

if __name__ == "__main__":
    build_application()