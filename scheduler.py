"""
Scheduler - Programador de tareas para noticiario diario
========================================================

Este módulo implementa el scheduler que:

- Programa el noticiario diario a una hora configurable
- Ejecuta el grafo LangGraph en modo "daily" para todos los chats suscritos
- Usa APScheduler para la programación de tareas
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class NewsScheduler:
    """
    Programador de tareas para el servicio de noticias.
    
    Ejecuta el noticiario diario a la hora configurada
    para todos los chats suscritos.
    """
    
    def __init__(
        self,
        daily_time: str = "08:00",
        timezone: str = "Europe/Madrid"
    ):
        """
        Inicializa el scheduler.
        
        Args:
            daily_time: Hora del noticiario diario (formato HH:MM)
            timezone: Zona horaria para la programación
        """
        self.daily_time = daily_time
        self.timezone = timezone
        
        # Parsear hora y minuto
        try:
            hour, minute = map(int, daily_time.split(":"))
            self.daily_hour = hour
            self.daily_minute = minute
        except ValueError:
            logger.warning(f"[Scheduler] Hora inválida: {daily_time}, usando 08:00")
            self.daily_hour = 8
            self.daily_minute = 0
        
        # Inicializar scheduler (BackgroundScheduler funciona sin event loop)
        self.scheduler = BackgroundScheduler(timezone=timezone)
        
        # Callback para ejecutar el noticiario
        self._daily_callback: Callable | None = None
        
        logger.info(
            f"[Scheduler] Configurado para {self.daily_hour:02d}:{self.daily_minute:02d} "
            f"({timezone})"
        )
    
    def set_daily_callback(self, callback: Callable) -> None:
        """
        Establece el callback que se ejecutará para el noticiario diario.
        
        Args:
            callback: Función async que recibe chat_id y ejecuta el noticiario
        """
        self._daily_callback = callback
        logger.info("[Scheduler] Callback diario configurado")
    
    def start(self) -> None:
        """Inicia el scheduler."""
        if not self._daily_callback:
            logger.warning("[Scheduler] No hay callback configurado, el scheduler no hará nada")
        
        # Programar tarea diaria
        self.scheduler.add_job(
            self._run_daily_news,
            CronTrigger(
                hour=self.daily_hour,
                minute=self.daily_minute,
                timezone=self.timezone
            ),
            id="daily_news",
            name="Noticiario Diario",
            replace_existing=True
        )
        
        # Iniciar scheduler
        self.scheduler.start()
        
        logger.info(
            f"[Scheduler] Iniciado. Próxima ejecución: "
            f"{self.scheduler.get_job('daily_news').next_run_time}"
        )
    
    def stop(self) -> None:
        """Detiene el scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("[Scheduler] Detenido")
    
    def _run_daily_news(self) -> None:
        """
        Ejecuta el noticiario diario para todos los chats suscritos.
        
        Esta función es llamada por el scheduler a la hora programada.
        Usa asyncio.run() para ejecutar el callback async.
        """
        logger.info("[Scheduler] Ejecutando noticiario diario...")
        
        if not self._daily_callback:
            logger.error("[Scheduler] No hay callback configurado")
            return
        
        try:
            # Ejecutar la función async en un nuevo event loop
            asyncio.run(self._run_daily_news_async())
        except Exception as e:
            logger.error(f"[Scheduler] Error ejecutando noticiario diario: {e}")
    
    async def _run_daily_news_async(self) -> None:
        """Versión async de _run_daily_news."""
        try:
            # Obtener lista de chats suscritos
            from persistence import StateStore
            store = StateStore()
            chat_ids = store.get_all_active_chats()
            
            if not chat_ids:
                logger.info("[Scheduler] No hay chats suscritos")
                return
            
            logger.info(f"[Scheduler] Generando noticiario para {len(chat_ids)} chats")
            
            # Ejecutar para cada chat
            for chat_id in chat_ids:
                try:
                    await self._daily_callback(chat_id)
                    logger.info(f"[Scheduler] Noticiario generado para chat_id={chat_id}")
                except Exception as e:
                    logger.error(f"[Scheduler] Error en chat_id={chat_id}: {e}")
            
            logger.info("[Scheduler] Noticiario diario completado")
            
        except Exception as e:
            logger.error(f"[Scheduler] Error ejecutando noticiario diario: {e}")
    
    async def run_now(self, chat_id: int) -> None:
        """
        Ejecuta el noticiario inmediatamente para un chat específico.
        
        Args:
            chat_id: ID del chat para el que generar el noticiario
        """
        if not self._daily_callback:
            logger.error("[Scheduler] No hay callback configurado")
            return
        
        logger.info(f"[Scheduler] Ejecutando noticiario bajo demanda para chat_id={chat_id}")
        
        try:
            await self._daily_callback(chat_id)
        except Exception as e:
            logger.error(f"[Scheduler] Error ejecutando noticiario: {e}")
    
    def get_next_run_time(self) -> datetime | None:
        """
        Obtiene la próxima hora de ejecución del noticiario.
        
        Returns:
            Datetime de la próxima ejecución o None
        """
        job = self.scheduler.get_job("daily_news")
        if job:
            return job.next_run_time
        return None
    
    def get_status(self) -> dict:
        """
        Obtiene el estado del scheduler.
        
        Returns:
            Diccionario con información del estado
        """
        job = self.scheduler.get_job("daily_news")
        
        return {
            "running": self.scheduler.running,
            "daily_time": f"{self.daily_hour:02d}:{self.daily_minute:02d}",
            "timezone": self.timezone,
            "next_run": str(job.next_run_time) if job else None,
            "callback_configured": self._daily_callback is not None,
        }


# Instancia global del scheduler
_scheduler_instance: NewsScheduler | None = None


def get_scheduler(
    daily_time: str | None = None,
    timezone: str | None = None
) -> NewsScheduler:
    """
    Obtiene la instancia del scheduler (singleton).
    
    Args:
        daily_time: Hora del noticiario (solo se usa en la primera llamada)
        timezone: Zona horaria (solo se usa en la primera llamada)
        
    Returns:
        Instancia del scheduler
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = NewsScheduler(
            daily_time=daily_time or os.getenv("SCHEDULER_TIME", "08:00"),
            timezone=timezone or os.getenv("SCHEDULER_TIMEZONE", "Europe/Madrid")
        )
    
    return _scheduler_instance
