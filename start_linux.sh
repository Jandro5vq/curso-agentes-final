#!/bin/bash
# Script de demostración para Linux - Ventanas de terminal separadas
# =================================================================

echo "🐧 NEWS SERVICE - DEMO LINUX CON VENTANAS SEPARADAS"
echo "=================================================="
echo ""

# Verificar que estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Este script está diseñado para Linux"
    exit 1
fi

# Verificar que existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "❌ No se encontró el entorno virtual (.venv)"
    echo "💡 Ejecuta primero: python3 -m venv .venv"
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "❌ No se encontró el archivo .env"
    echo "💡 Copia .env.example a .env y configura tus API keys"
    exit 1
fi

echo "✅ Verificaciones completadas"
echo ""

# Detectar terminal disponible
detect_terminal() {
    local terminals=("gnome-terminal" "konsole" "xfce4-terminal" "terminator" "xterm" "urxvt" "alacritty")
    
    for terminal in "${terminals[@]}"; do
        if command -v "$terminal" &> /dev/null; then
            echo "$terminal"
            return 0
        fi
    done
    
    return 1
}

TERMINAL=$(detect_terminal)

if [ $? -eq 0 ]; then
    echo "🖥️  Terminal detectado: $TERMINAL"
    echo "📋 Se abrirán ventanas separadas para:"
    echo "   1. 🤖 News Service (Agentes Multi-Agent)"
    echo "   2. 📊 Dashboard Web"
    echo ""
    
    # Activar entorno virtual y ejecutar el script principal
    echo "🚀 Iniciando servicios en ventanas separadas..."
    source .venv/bin/activate
    python start.py
    
else
    echo "⚠️  No se encontró terminal gráfico disponible"
    echo "💡 Instala uno de estos terminales para ver ventanas separadas:"
    echo "   - Ubuntu/GNOME: sudo apt install gnome-terminal"
    echo "   - KDE: sudo apt install konsole" 
    echo "   - XFCE: sudo apt install xfce4-terminal"
    echo "   - General: sudo apt install xterm"
    echo ""
    echo "🔄 Ejecutando en modo background..."
    source .venv/bin/activate
    python start.py
fi