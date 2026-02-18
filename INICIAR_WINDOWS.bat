@echo off
title JUSTICIA.ar - Iniciando Sistema
color 0A

echo ========================================
echo   JUSTICIA.ar - Sistema Automatico
echo ========================================
echo.
echo Iniciando servidor backend...
echo.
echo IMPORTANTE: NO CIERRES ESTA VENTANA
echo.
echo El navegador se abrira automaticamente
echo en unos segundos...
echo.
echo ========================================
echo.

REM Cambiar al directorio backend
cd /d "%~dp0backend"

REM Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo.
    echo Por favor instala Python desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM Verificar si las dependencias estan instaladas
echo Verificando dependencias...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias necesarias...
    pip install flask flask-cors
    echo.
)

REM Verificar si existe la base de datos
if not exist "justicia.db" (
    echo Inicializando base de datos...
    python init_db.py
    echo.
)

REM Esperar 2 segundos
timeout /t 2 /nobreak >nul

REM Abrir el frontend en el navegador predeterminado
echo Abriendo interfaz en el navegador...
start "" "%~dp0frontend\index.html"

REM Iniciar el servidor
echo.
echo ========================================
echo   SERVIDOR INICIADO EN http://localhost:5000
echo.
echo   Para DETENER el servidor:
echo   Cierra esta ventana o presiona Ctrl+C
echo ========================================
echo.

python app.py

REM Si el servidor se detiene, mantener la ventana abierta
pause
