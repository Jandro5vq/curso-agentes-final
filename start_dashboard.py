#!/usr/bin/env python3
"""
Script para iniciar el dashboard web del servicio de noticias.
"""

import os
import sys
import logging
import subprocess
import webbrowser
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

def check_requirements():
    """Verifica que Flask esté instalado."""
    try:
        import flask
        return True
    except ImportError:
        return False

def install_flask():
    """Instala Flask si no está disponible."""
    print("📦 Flask no encontrado, instalando...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        return True
    except subprocess.CalledProcessError:
        return False

def start_dashboard():
    """Inicia el dashboard."""
    # Configurar variables de entorno
    os.environ.setdefault('FLASK_SECRET_KEY', 'news-service-dashboard-2024')
    os.environ.setdefault('DASHBOARD_PORT', '5000')
    os.environ.setdefault('FLASK_DEBUG', 'false')
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Iniciando News Service Dashboard...")
    print(f"📍 URL: http://localhost:{os.environ['DASHBOARD_PORT']}")
    print("🛑 Presiona Ctrl+C para detener")
    print("-" * 50)
    
    # Abrir navegador automáticamente
    try:
        webbrowser.open(f"http://localhost:{os.environ['DASHBOARD_PORT']}")
    except:
        pass
    
    # Importar y ejecutar la app
    from dashboard.app import app
    
    port = int(os.environ['DASHBOARD_PORT'])
    debug = os.environ['FLASK_DEBUG'].lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    print("📰 News Service Dashboard Starter")
    print("================================")
    
    # Verificar requisitos
    if not check_requirements():
        if not install_flask():
            print("❌ Error: No se pudo instalar Flask")
            sys.exit(1)
    
    try:
        start_dashboard()
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido")
    except Exception as e:
        print(f"❌ Error iniciando dashboard: {e}")
        sys.exit(1)