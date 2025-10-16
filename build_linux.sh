#!/bin/bash

echo "========================================"
echo "   CONSTRUYENDO BIBLIOTECA IA - LINUX"
echo "========================================"
echo

echo "📦 Instalando dependencias..."
pip3 install -r requirements.txt

echo
echo "🔨 Construyendo ejecutable..."
python3 build.py

echo
echo "========================================"
echo "          CONSTRUCCIÓN COMPLETADA"
echo "========================================"
echo
echo "📦 Ejecutable: dist/BibliotecaIA"
echo
echo "📋 Para distribuir la aplicación:"
echo "   - Copia el archivo dist/BibliotecaIA"
echo "   - Copia la carpeta config/"
echo "   - Copia la carpeta resources/"
echo "   - La carpeta data/ se creará automáticamente"
echo
echo "🔧 Para hacer ejecutable: chmod +x dist/BibliotecaIA"