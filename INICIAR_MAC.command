#!/bin/bash

# Obtener el directorio donde está este script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Función para imprimir con color
print_color() {
    echo -e "\033[0;32m$1\033[0m"
}

print_error() {
    echo -e "\033[0;31m$1\033[0m"
}

clear
print_color "========================================"
print_color "  JUSTICIA.ar - Sistema Automático"
print_color "========================================"
echo ""
print_color "Iniciando servidor backend..."
echo ""
print_color "IMPORTANTE: NO CIERRES ESTA VENTANA"
echo ""
print_color "El navegador se abrirá automáticamente"
print_color "en unos segundos..."
echo ""
print_color "========================================"
echo ""

# Ir al directorio backend
cd "$DIR/backend"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    print_error "ERROR: Python 3 no está instalado"
    echo ""
    echo "Por favor instala Python 3 desde: https://www.python.org/downloads/"
    echo ""
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Verificar si las dependencias están instaladas
print_color "Verificando dependencias..."
if ! python3 -c "import flask" 2>/dev/null; then
    print_color "Instalando dependencias necesarias..."
    pip3 install flask flask-cors
    echo ""
fi

# Verificar si existe la base de datos
if [ ! -f "justicia.db" ]; then
    print_color "Inicializando base de datos..."
    python3 init_db.py
    echo ""
fi

# Esperar 2 segundos
sleep 2

# Abrir el frontend en el navegador predeterminado
print_color "Abriendo interfaz en el navegador..."
open "$DIR/frontend/index.html"

# Iniciar el servidor
echo ""
print_color "========================================"
print_color "  SERVIDOR INICIADO EN http://localhost:5000"
echo ""
print_color "  Para DETENER el servidor:"
print_color "  Cierra esta ventana o presiona Ctrl+C"
print_color "========================================"
echo ""

python3 app.py

# Si el servidor se detiene, mantener la ventana abierta
read -p "Presiona Enter para salir..."
