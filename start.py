#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Script - Inicia el servicio de agentes y el dashboard simultáneamente
===========================================================================

Este script inicia ambos servicios en paralelo:
1. News Service (main_multiagent.py) - Servicio principal de agentes
2. Dashboard Web (dashboard) - Interfaz de monitoreo

Ejecuta: python start.py
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
import webbrowser
from pathlib import Path

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import locale
    # Forzar UTF-8 para evitar problemas de encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Cargar variables de entorno desde .env
def load_env_file():
    """Carga variables de entorno desde archivo .env"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ Variables de entorno cargadas desde {env_path}")
    else:
        print(f"⚠️  Archivo .env no encontrado en {env_path}")

# Cargar .env al importar
load_env_file()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ServiceManager:
    """Gestor para iniciar y controlar ambos servicios."""
    
    def __init__(self):
        self.processes = {}
        self.shutdown_event = threading.Event()
        self.root_path = Path(__file__).parent
        
    def start_news_service(self):
        """Inicia el servicio principal de noticias."""
        try:
            logger.info("Iniciando News Service (Agentes Multi-Agent)...")
            
            # Configurar variables de entorno necesarias
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.root_path)
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Comando para iniciar el servicio
            cmd = [sys.executable, "main_multiagent.py"]
            
            # Detectar sistema operativo y abrir ventana apropiada
            if sys.platform.startswith('win'):
                # Windows: Nueva ventana de consola
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root_path,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            elif sys.platform.startswith('linux'):
                # Linux: Detectar terminal disponible y abrir nueva ventana
                terminal_cmd = self._get_linux_terminal_command(cmd, "News Service - Agentes Multi-Agent")
                if terminal_cmd:
                    process = subprocess.Popen(terminal_cmd, cwd=self.root_path, env=env)
                else:
                    # Fallback: ejecutar en background
                    logger.warning("No se encontró terminal gráfico, ejecutando en background")
                    process = subprocess.Popen(cmd, cwd=self.root_path, env=env)
            else:
                # macOS u otros: ejecutar en background
                process = subprocess.Popen(cmd, cwd=self.root_path, env=env)
            
            self.processes['news_service'] = process
            logger.info("News Service iniciado en ventana separada")
            
        except Exception as e:
            logger.error(f"Error iniciando News Service: {e}")
    
    def start_dashboard(self):
        """Inicia el dashboard web."""
        try:
            logger.info("Iniciando Dashboard Web...")
            
            # Configurar variables de entorno para dashboard
            env = os.environ.copy()
            env.update({
                'FLASK_SECRET_KEY': 'news-service-dashboard-2024',
                'DASHBOARD_PORT': '5000',
                'FLASK_DEBUG': 'false',
                'PYTHONPATH': str(self.root_path),
                'PYTHONIOENCODING': 'utf-8'
            })
            
            # Comando para iniciar el dashboard
            cmd = [sys.executable, "start_dashboard.py"]
            
            # Detectar sistema operativo y abrir ventana apropiada
            if sys.platform.startswith('win'):
                # Windows: Nueva ventana de consola
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root_path,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            elif sys.platform.startswith('linux'):
                # Linux: Detectar terminal disponible y abrir nueva ventana
                terminal_cmd = self._get_linux_terminal_command(cmd, "News Service - Dashboard Web")
                if terminal_cmd:
                    process = subprocess.Popen(terminal_cmd, cwd=self.root_path, env=env)
                else:
                    # Fallback: ejecutar en background
                    logger.warning("No se encontró terminal gráfico, ejecutando en background")
                    process = subprocess.Popen(cmd, cwd=self.root_path, env=env)
            else:
                # macOS u otros: ejecutar en background
                process = subprocess.Popen(cmd, cwd=self.root_path, env=env)
            
            self.processes['dashboard'] = process
            logger.info("Dashboard iniciado en ventana separada")
            
            # Esperar un momento y abrir navegador
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:5000")
                logger.info("Dashboard abierto en navegador: http://localhost:5000")
            except:
                logger.info("Dashboard disponible en: http://localhost:5000")
                
        except Exception as e:
            logger.error(f"Error iniciando Dashboard: {e}")
    
    def _get_linux_terminal_command(self, cmd, title):
        """
        Detecta y retorna el comando apropiado para abrir una nueva ventana de terminal en Linux.
        
        Args:
            cmd: Comando a ejecutar [python, script.py]
            title: Título para la ventana
            
        Returns:
            Lista con el comando completo para abrir terminal o None si no encuentra
        """
        # Lista de terminales comunes en Linux con sus comandos
        terminals = [
            # GNOME Terminal (Ubuntu, Fedora, etc.)
            ['gnome-terminal', '--title', title, '--', 'bash', '-c', 
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
            
            # KDE Konsole 
            ['konsole', '--title', title, '-e', 'bash', '-c',
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
            
            # XFCE Terminal
            ['xfce4-terminal', '--title', title, '-e', 'bash', '-c',
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
            
            # Terminator
            ['terminator', '--title', title, '-e', 'bash', '-c',
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
            
            # xterm (disponible en casi todos los sistemas)
            ['xterm', '-title', title, '-e', 'bash', '-c',
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
            
            # urxvt (rxvt-unicode)
            ['urxvt', '-title', title, '-e', 'bash', '-c',
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
            
            # Alacritty
            ['alacritty', '--title', title, '-e', 'bash', '-c',
             f"cd {self.root_path} && {' '.join(cmd)}; exec bash"],
        ]
        
        # Probar cada terminal hasta encontrar uno disponible
        for terminal_cmd in terminals:
            try:
                # Verificar si el terminal está disponible
                result = subprocess.run(['which', terminal_cmd[0]], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Usando terminal: {terminal_cmd[0]}")
                    return terminal_cmd
            except:
                continue
        
        logger.warning("No se encontró ningún terminal gráfico disponible")
        return None
    
    def check_requirements(self):
        """Verifica que las dependencias estén instaladas."""
        try:
            # Verificar módulos críticos
            import flask
            import telegram
            import openai
            import langchain
            import langgraph
            
            logger.info("Todas las dependencias verificadas")
            return True
            
        except ImportError as e:
            logger.error(f"Dependencia faltante: {e}")
            logger.info("Ejecuta: pip install -r requirements.txt")
            return False
    
    def check_environment(self):
        """Verifica las variables de entorno críticas."""
        required_vars = [
            'OPENAI_API_KEY',
            'TELEGRAM_BOT_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
            logger.info("Configura tu archivo .env con las API keys necesarias")
            return False
        
        logger.info("Variables de entorno verificadas")
        return True
    
    def start_all_services(self):
        """Inicia todos los servicios."""
        print("=" * 60)
        print("LA IA DICE - NEWS SERVICE LAUNCHER")
        print("=" * 60)
        print("Servicio Multi-Agente + Dashboard Web")
        
        # Mostrar información específica del sistema
        if sys.platform.startswith('win'):
            print("Sistema: Windows - Se abrirán ventanas de consola separadas")
        elif sys.platform.startswith('linux'):
            print("Sistema: Linux - Se intentará abrir ventanas de terminal separadas")
        else:
            print(f"Sistema: {sys.platform} - Ejecución en background")
            
        print("=" * 60)
        
        # Verificaciones previas
        if not self.check_requirements():
            return False
            
        if not self.check_environment():
            return False
        
        # Iniciar servicios
        self.start_dashboard()
        time.sleep(2)  # Dar tiempo al dashboard para iniciar
        self.start_news_service()
        
        print("=" * 60)
        print("SERVICIOS INICIADOS CORRECTAMENTE")
        print("Telegram Bot: Activo y escuchando")
        print("Dashboard Web: http://localhost:5000")
        print("Presiona Ctrl+C para detener ambos servicios")
        
        # Información específica sobre las ventanas
        if sys.platform.startswith('win'):
            print("Ventanas: Cada servicio tiene su propia ventana de consola")
        elif sys.platform.startswith('linux'):
            print("Ventanas: Cada servicio tiene su propia ventana de terminal")
        
        print("=" * 60)
        
        return True
    
    def stop_all_services(self):
        """Detiene todos los servicios."""
        logger.info("Deteniendo servicios...")
        self.shutdown_event.set()
        
        for name, process in self.processes.items():
            try:
                logger.info(f"Deteniendo {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Forzando cierre de {name}...")
                process.kill()
                process.wait()
            except Exception as e:
                logger.error(f"Error deteniendo {name}: {e}")
        
        logger.info("Todos los servicios detenidos")
    
    def wait_for_shutdown(self):
        """Espera la señal de shutdown."""
        try:
            while not self.shutdown_event.is_set():
                time.sleep(1)
                
                # Verificar si algún proceso murió inesperadamente
                dead_processes = []
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        dead_processes.append(name)
                
                if dead_processes:
                    logger.warning(f"Procesos terminados: {', '.join(dead_processes)}")
                    break
                        
        except KeyboardInterrupt:
            logger.info("Ctrl+C detectado, iniciando shutdown...")


def signal_handler(signum, frame):
    """Maneja las señales del sistema."""
    logger.info("Señal de shutdown recibida")
    manager.shutdown_event.set()


def main():
    """Función principal."""
    global manager
    
    manager = ServiceManager()
    
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Iniciar todos los servicios
        if manager.start_all_services():
            # Esperar hasta shutdown
            manager.wait_for_shutdown()
        
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        
    finally:
        # Cleanup
        manager.stop_all_services()
        print("\n¡Hasta pronto!")


if __name__ == "__main__":
    main()