@echo off
echo ========================================
echo    CONSTRUYENDO BIBLIOTECA IA - WINDOWS
echo ========================================
echo.

echo 📦 Instalando dependencias...
pip install -r requirements.txt

echo.
echo 🔨 Construyendo ejecutable...
python build.py

echo.
echo ========================================
echo            CONSTRUCCIÓN COMPLETADA
echo ========================================
echo.
echo 📦 Ejecutable: dist\BibliotecaIA.exe
echo.
echo 📋 Para distribuir la aplicación:
echo   1. Copia el archivo dist\BibliotecaIA.exe
echo   2. Copia la carpeta config\
echo   3. Copia la carpeta resources\
echo   4. La carpeta data\ se creará automáticamente
echo.
pause