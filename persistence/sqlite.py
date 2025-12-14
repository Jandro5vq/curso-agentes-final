"""
SQLite State Store - Persistencia del estado en SQLite
======================================================

Este módulo implementa la persistencia del NewsState usando SQLite.

Funcionalidades:
- Guarda el estado completo como JSON
- Clave compuesta: (chat_id, date)
- Operaciones: load_state, save_state
- Carga el estado antes de cada ejecución
- Guarda el estado al finalizar
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class StateStore:
    """
    Almacén de estado persistente usando SQLite.
    
    Cada entrada está indexada por (chat_id, date) para mantener
    una historia diaria por chat.
    """
    
    def __init__(self, db_path: str = "./data/news_state.db"):
        """
        Inicializa el almacén de estado.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self._init_db()
        
        logger.info(f"[StateStore] Base de datos inicializada: {self.db_path}")
    
    def _init_db(self) -> None:
        """Crea las tablas necesarias si no existen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla principal de estados diarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_states (
                    chat_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, date)
                )
            """)
            
            # Índice para búsquedas por chat_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_states_chat_id 
                ON daily_states(chat_id)
            """)
            
            # Índice para búsquedas por fecha
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_states_date 
                ON daily_states(date)
            """)
            
            # Tabla de historial de conversaciones (para consultas rápidas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_chat_date 
                ON conversation_history(chat_id, date)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones a la base de datos."""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def load_state(self, chat_id: int, date: str) -> dict[str, Any] | None:
        """
        Carga el estado para un chat y fecha específicos.
        
        Args:
            chat_id: ID del chat de Telegram
            date: Fecha en formato YYYY-MM-DD
            
        Returns:
            Estado deserializado o None si no existe
        """
        logger.debug(f"[StateStore] Cargando estado para chat_id={chat_id}, date={date}")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT state_json FROM daily_states WHERE chat_id = ? AND date = ?",
                (chat_id, date)
            )
            
            row = cursor.fetchone()
            
            if row:
                try:
                    state = json.loads(row["state_json"])
                    logger.info(f"[StateStore] Estado cargado para chat_id={chat_id}, date={date}")
                    return state
                except json.JSONDecodeError as e:
                    logger.error(f"[StateStore] Error deserializando estado: {e}")
                    return None
            
            logger.debug(f"[StateStore] No existe estado para chat_id={chat_id}, date={date}")
            return None
    
    def save_state(self, chat_id: int, date: str, state: dict[str, Any]) -> bool:
        """
        Guarda el estado para un chat y fecha específicos.
        
        Args:
            chat_id: ID del chat de Telegram
            date: Fecha en formato YYYY-MM-DD
            state: Estado a guardar (NewsState)
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        logger.debug(f"[StateStore] Guardando estado para chat_id={chat_id}, date={date}")
        
        try:
            state_json = json.dumps(state, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"[StateStore] Error serializando estado: {e}")
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO daily_states (chat_id, date, state_json, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (chat_id, date) 
                    DO UPDATE SET 
                        state_json = excluded.state_json,
                        updated_at = CURRENT_TIMESTAMP
                """, (chat_id, date, state_json))
                
                conn.commit()
                logger.info(f"[StateStore] Estado guardado para chat_id={chat_id}, date={date}")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"[StateStore] Error guardando estado: {e}")
                conn.rollback()
                return False
    
    def delete_state(self, chat_id: int, date: str) -> bool:
        """
        Elimina el estado para un chat y fecha específicos.
        
        Args:
            chat_id: ID del chat de Telegram
            date: Fecha en formato YYYY-MM-DD
            
        Returns:
            True si se eliminó correctamente
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "DELETE FROM daily_states WHERE chat_id = ? AND date = ?",
                    (chat_id, date)
                )
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"[StateStore] Estado eliminado para chat_id={chat_id}, date={date}")
                
                return deleted
                
            except sqlite3.Error as e:
                logger.error(f"[StateStore] Error eliminando estado: {e}")
                return False
    
    def get_chat_history(
        self, 
        chat_id: int, 
        days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Obtiene el historial de estados de un chat.
        
        Args:
            chat_id: ID del chat de Telegram
            days: Número de días hacia atrás
            
        Returns:
            Lista de estados ordenados por fecha descendente
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT date, state_json 
                FROM daily_states 
                WHERE chat_id = ? 
                AND date >= date('now', ?)
                ORDER BY date DESC
            """, (chat_id, f'-{days} days'))
            
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                try:
                    state = json.loads(row["state_json"])
                    history.append({
                        "date": row["date"],
                        "state": state
                    })
                except json.JSONDecodeError:
                    continue
            
            return history
    
    def get_all_active_chats(self) -> list[int]:
        """
        Obtiene todos los chat_ids que tienen estados guardados.
        
        Returns:
            Lista de chat_ids únicos
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT chat_id FROM daily_states")
            
            return [row["chat_id"] for row in cursor.fetchall()]
    
    def add_conversation_message(
        self,
        chat_id: int,
        date: str,
        role: str,
        content: str
    ) -> bool:
        """
        Añade un mensaje al historial de conversación.
        
        Args:
            chat_id: ID del chat
            date: Fecha del mensaje
            role: 'user' o 'assistant'
            content: Contenido del mensaje
            
        Returns:
            True si se añadió correctamente
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO conversation_history (chat_id, date, role, content)
                    VALUES (?, ?, ?, ?)
                """, (chat_id, date, role, content))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                logger.error(f"[StateStore] Error añadiendo mensaje: {e}")
                return False
    
    def get_conversation(
        self,
        chat_id: int,
        date: str,
        limit: int = 50
    ) -> list[dict[str, str]]:
        """
        Obtiene la conversación de un chat para una fecha.
        
        Args:
            chat_id: ID del chat
            date: Fecha de la conversación
            limit: Número máximo de mensajes
            
        Returns:
            Lista de mensajes [{"role": str, "content": str}, ...]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, content 
                FROM conversation_history 
                WHERE chat_id = ? AND date = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (chat_id, date, limit))
            
            return [
                {"role": row["role"], "content": row["content"]}
                for row in cursor.fetchall()
            ]
    
    def cleanup_old_states(self, days_to_keep: int = 30) -> int:
        """
        Elimina estados más antiguos que el número de días especificado.
        
        Args:
            days_to_keep: Días de historia a mantener
            
        Returns:
            Número de registros eliminados
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Eliminar estados antiguos
                cursor.execute("""
                    DELETE FROM daily_states 
                    WHERE date < date('now', ?)
                """, (f'-{days_to_keep} days',))
                
                states_deleted = cursor.rowcount
                
                # Eliminar conversaciones antiguas
                cursor.execute("""
                    DELETE FROM conversation_history 
                    WHERE date < date('now', ?)
                """, (f'-{days_to_keep} days',))
                
                conv_deleted = cursor.rowcount
                
                conn.commit()
                
                total_deleted = states_deleted + conv_deleted
                if total_deleted > 0:
                    logger.info(
                        f"[StateStore] Limpieza: {states_deleted} estados, "
                        f"{conv_deleted} mensajes eliminados"
                    )
                
                return total_deleted
                
            except sqlite3.Error as e:
                logger.error(f"[StateStore] Error en limpieza: {e}")
                return 0
    
    def get_stats(self) -> dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de estados
            cursor.execute("SELECT COUNT(*) as count FROM daily_states")
            total_states = cursor.fetchone()["count"]
            
            # Total de chats únicos
            cursor.execute("SELECT COUNT(DISTINCT chat_id) as count FROM daily_states")
            total_chats = cursor.fetchone()["count"]
            
            # Total de mensajes
            cursor.execute("SELECT COUNT(*) as count FROM conversation_history")
            total_messages = cursor.fetchone()["count"]
            
            # Estado más reciente
            cursor.execute("""
                SELECT MAX(updated_at) as latest FROM daily_states
            """)
            row = cursor.fetchone()
            latest_update = row["latest"] if row else None
            
            return {
                "total_states": total_states,
                "total_chats": total_chats,
                "total_messages": total_messages,
                "latest_update": latest_update,
                "db_path": str(self.db_path),
            }
