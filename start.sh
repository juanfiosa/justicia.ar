#!/bin/bash

# JUSTICIA.ar - Script de Inicio Rápido

echo "=========================================="
echo "  JUSTICIA.ar - Sistema de Resolución"
echo "  Asistida por IA"
echo "=========================================="
echo ""

# Verificar si la base de datos existe
if [ ! -f "justicia.db" ]; then
    echo "⚠️  Base de datos no encontrada. Inicializando..."
    python3 init_db.py
    echo ""
fi

echo "🚀 Iniciando servidor backend..."
echo ""
echo "📡 API disponible en: http://localhost:5000"
echo "🌐 Frontend: Abre frontend/index.html en tu navegador"
echo ""
echo "Para detener el servidor, presiona Ctrl+C"
echo ""
echo "=========================================="
echo ""

# Iniciar servidor Flask
python3 app.py
