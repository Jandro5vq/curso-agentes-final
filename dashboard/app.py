# Dashboard Web Minimal para News Service
# =======================================

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
import sqlite3
import logging

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'news-service-dashboard-2024')


class DashboardService:
    """Servicio para obtener datos del dashboard."""
    
    @staticmethod
    def get_system_stats():
        """Obtiene estadísticas generales del sistema."""
        try:
            # Por ahora, retornamos datos de ejemplo para demostración
            # En un entorno real, estos vendrían de la base de datos actual
            return {
                'total_conversations': 42,
                'conversations_24h': 7,
                'conversation_states': {
                    'active': 3,
                    'completed': 4
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total_conversations': 0,
                'conversations_24h': 0,
                'conversation_states': {}
            }
    
    @staticmethod
    def get_recent_conversations(limit=10):
        """Obtiene conversaciones recientes."""
        try:
            # Datos de ejemplo para demostración
            from datetime import datetime, timedelta
            now = datetime.now()
            
            conversations = []
            for i in range(min(limit, 5)):  # Máximo 5 ejemplos
                time_offset = timedelta(minutes=i*15)
                timestamp = (now - time_offset).strftime('%Y-%m-%d %H:%M:%S')
                
                conversations.append({
                    'user_id': f'user_{12345678 + i}',
                    'state': 'completed' if i % 2 == 0 else 'processing',
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    'duration': f'0:0{i+1}:3{i}'
                })
                
            return conversations
                
        except Exception as e:
            logger.error(f"Error obteniendo conversaciones recientes: {e}")
            return []
    
    @staticmethod
    def get_error_logs(limit=20):
        """Obtiene logs de errores recientes."""
        # Por simplicidad, retornamos datos de ejemplo
        # En un entorno real, esto vendría de archivos de log
        return [
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': 'Sistema iniciado correctamente',
                'module': 'main_multiagent'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'WARNING',
                'message': 'API rate limit approaching',
                'module': 'news_client'
            }
        ]
    
    @staticmethod
    def _calculate_duration(created_at, updated_at):
        """Calcula la duración de una conversación."""
        try:
            if isinstance(created_at, str):
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created = created_at
                
            if isinstance(updated_at, str):
                updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                updated = updated_at
            
            duration = updated - created
            return str(duration).split('.')[0]  # Sin microsegundos
            
        except:
            return "0:00:00"


@app.route('/')
def dashboard():
    """Página principal del dashboard."""
    stats = DashboardService.get_system_stats()
    recent_conversations = DashboardService.get_recent_conversations()
    return render_template('dashboard.html', 
                         stats=stats, 
                         conversations=recent_conversations)


@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas en tiempo real."""
    return jsonify(DashboardService.get_system_stats())


@app.route('/api/conversations')
def api_conversations():
    """API endpoint para conversaciones recientes."""
    limit = request.args.get('limit', 10, type=int)
    return jsonify(DashboardService.get_recent_conversations(limit))


@app.route('/api/logs')
def api_logs():
    """API endpoint para logs del sistema."""
    return jsonify(DashboardService.get_error_logs())


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'news-service-dashboard'
    })


if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Iniciando dashboard en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)