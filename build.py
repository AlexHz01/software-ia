#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path

def build_application():
    """Construir la aplicación para diferentes plataformas"""
    system = platform.system().lower()
    
    print(f"🔨 Construyendo aplicación para {system.upper()}...")
    print(f"📁 Directorio actual: {Path('.').absolute()}")
    
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
        print("✅ Usando icono personalizado")
    else:
        print("⚠️  No se encontró icono, usando predeterminado")
    
    # Agregar datos según plataforma
    if system == "windows":
        args.extend([
            "--add-data=config;config",
            "--add-data=resources;resources"
        ])
    else:  # Linux/macOS
        args.extend([
            "--add-data=config:config",
            "--add-data=resources:resources"
        ])
    
    # Archivo principal
    args.append("src/main.py")
    
    try:
        # Ejecutar PyInstaller
        print("🚀 Ejecutando PyInstaller...")
        result = subprocess.run(args, check=True, capture_output=True, text=True, shell=(system == "windows"))
        
        # Verificar resultado
        exe_name = "BibliotecaIA.exe" if system == "windows" else "BibliotecaIA"
        dist_path = Path("dist") / exe_name
        
        if dist_path.exists():
            file_size = dist_path.stat().st_size / (1024 * 1024)  # MB
            print("✅ ¡Aplicación construida exitosamente!")
            print(f"📦 Ejecutable: {dist_path.absolute()}")
            print(f"📊 Tamaño: {file_size:.2f} MB")
            
            # Listar contenido de dist/
            print("\n📁 Contenido de dist/:")
            for item in Path("dist").iterdir():
                print(f"   - {item.name}")
                
        else:
            print("❌ No se pudo encontrar el ejecutable")
            if result.stderr:
                print("Errores:")
                print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error durante la construcción: {e}")
        if e.stderr:
            print(f"Detalles: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ PyInstaller no está instalado")
        sys.exit(1)

if __name__ == "__main__":
    build_application()