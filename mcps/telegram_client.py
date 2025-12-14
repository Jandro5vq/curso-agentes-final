"""
MCP Telegram Client - Cliente para interacción con Telegram
===========================================================

Este módulo implementa el cliente MCP de Telegram que proporciona:

- send_text(chat_id, text): Envía mensaje de texto
- send_audio(chat_id, audio_path): Envía archivo de audio

Utiliza python-telegram-bot para la comunicación.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TelegramClient:
    """
    Cliente MCP para interacción con Telegram.
    
    Proporciona métodos síncronos para enviar mensajes y audio,
    manejando internamente la asincronía de python-telegram-bot.
    """
    
    def __init__(self, bot_token: str | None = None):
        """
        Inicializa el cliente de Telegram.
        
        Args:
            bot_token: Token del bot de Telegram.
                      Si no se proporciona, se lee de TELEGRAM_BOT_TOKEN.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        if not self.bot_token:
            logger.warning("[TelegramClient] No se configuró TELEGRAM_BOT_TOKEN")
        
        self._bot = None
        self._initialized = False
        
        logger.info("[TelegramClient] Cliente Telegram configurado")
    
    def _ensure_initialized(self) -> bool:
        """
        Asegura que el bot esté inicializado.
        
        Returns:
            True si se inicializó correctamente
        """
        if self._initialized and self._bot:
            return True
        
        if not self.bot_token:
            logger.error("[TelegramClient] No hay token de bot configurado")
            return False
        
        try:
            from telegram import Bot
            self._bot = Bot(token=self.bot_token)
            self._initialized = True
            logger.info("[TelegramClient] Bot inicializado correctamente")
            return True
            
        except ImportError:
            logger.error("[TelegramClient] python-telegram-bot no está instalado")
            logger.error("[TelegramClient] Instala con: pip install python-telegram-bot")
            return False
            
        except Exception as e:
            logger.error(f"[TelegramClient] Error inicializando bot: {e}")
            return False
    
    def _run_async(self, coro: Any) -> Any:
        """
        Ejecuta una coroutine de forma síncrona.
        Requiere que nest_asyncio.apply() haya sido llamado al inicio del programa.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # nest_asyncio permite esto
                return loop.run_until_complete(coro)
            else:
                return asyncio.run(coro)
        except RuntimeError:
            # Crear nuevo loop si es necesario
            return asyncio.run(coro)

    def send_text(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None
    ) -> bool:
        """
        Envía un mensaje de texto a un chat.
        
        Args:
            chat_id: ID del chat de destino
            text: Texto del mensaje
            parse_mode: Modo de parseo ('Markdown', 'HTML', None)
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self._ensure_initialized():
            return False
        
        if not text or not text.strip():
            logger.warning("[TelegramClient] Texto vacío para enviar")
            return False
        
        logger.info(f"[TelegramClient] Enviando texto a chat_id={chat_id} ({len(text)} caracteres)")
        
        try:
            # Truncar texto si es muy largo (límite de Telegram: 4096 caracteres)
            if len(text) > 4096:
                text = text[:4090] + "..."
                logger.warning("[TelegramClient] Texto truncado por exceder límite")
            
            async def _send():
                return await self._bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode
                )
            
            self._run_async(_send())
            logger.info("[TelegramClient] Mensaje enviado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"[TelegramClient] Error enviando mensaje: {e}")
            return False
    
    async def send_text_async(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None
    ) -> bool:
        """
        Versión async de send_text para usar en contextos async.
        
        Args:
            chat_id: ID del chat de destino
            text: Texto del mensaje
            parse_mode: Modo de parseo ('Markdown', 'HTML', None)
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self._ensure_initialized():
            return False
        
        if not text or not text.strip():
            logger.warning("[TelegramClient] Texto vacío para enviar")
            return False
        
        logger.info(f"[TelegramClient] Enviando texto async a chat_id={chat_id} ({len(text)} caracteres)")
        
        try:
            # Truncar texto si es muy largo (límite de Telegram: 4096 caracteres)
            if len(text) > 4096:
                text = text[:4090] + "..."
                logger.warning("[TelegramClient] Texto truncado por exceder límite")
            
            await self._bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode
            )
            logger.info("[TelegramClient] Mensaje enviado correctamente (async)")
            return True
            
        except Exception as e:
            logger.error(f"[TelegramClient] Error enviando mensaje async: {e}")
            return False

    def send_audio(
        self,
        chat_id: int,
        audio_path: str,
        caption: str | None = None,
        title: str | None = None,
        performer: str | None = None
    ) -> bool:
        """
        Envía un archivo de audio a un chat.
        
        Args:
            chat_id: ID del chat de destino
            audio_path: Ruta al archivo de audio
            caption: Texto opcional para acompañar el audio
            title: Título del audio
            performer: Nombre del artista/performer
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self._ensure_initialized():
            return False
        
        audio_file = Path(audio_path)
        
        if not audio_file.exists():
            logger.error(f"[TelegramClient] Archivo de audio no encontrado: {audio_path}")
            return False
        
        file_size = audio_file.stat().st_size
        logger.info(f"[TelegramClient] Enviando audio a chat_id={chat_id} ({file_size / 1024:.1f} KB)")
        
        try:
            async def _send():
                with open(audio_file, 'rb') as audio:
                    return await self._bot.send_audio(
                        chat_id=chat_id,
                        audio=audio,
                        caption=caption,
                        title=title or "Podcast de Noticias",
                        performer=performer or "News Service",
                        parse_mode="Markdown" if caption else None
                    )
            
            self._run_async(_send())
            logger.info("[TelegramClient] Audio enviado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"[TelegramClient] Error enviando audio: {e}")
            return False
    
    def send_voice(
        self,
        chat_id: int,
        voice_path: str,
        caption: str | None = None
    ) -> bool:
        """
        Envía un mensaje de voz a un chat.
        
        Args:
            chat_id: ID del chat de destino
            voice_path: Ruta al archivo de voz (OGG preferido)
            caption: Texto opcional
            
        Returns:
            True si se envió correctamente
        """
        if not self._ensure_initialized():
            return False
        
        voice_file = Path(voice_path)
        
        if not voice_file.exists():
            logger.error(f"[TelegramClient] Archivo de voz no encontrado: {voice_path}")
            return False
        
        try:
            async def _send():
                with open(voice_file, 'rb') as voice:
                    return await self._bot.send_voice(
                        chat_id=chat_id,
                        voice=voice,
                        caption=caption
                    )
            
            self._run_async(_send())
            logger.info("[TelegramClient] Voz enviada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"[TelegramClient] Error enviando voz: {e}")
            return False
    
    def send_document(
        self,
        chat_id: int,
        document_path: str,
        caption: str | None = None
    ) -> bool:
        """
        Envía un documento a un chat.
        
        Args:
            chat_id: ID del chat de destino
            document_path: Ruta al documento
            caption: Texto opcional
            
        Returns:
            True si se envió correctamente
        """
        if not self._ensure_initialized():
            return False
        
        doc_file = Path(document_path)
        
        if not doc_file.exists():
            logger.error(f"[TelegramClient] Documento no encontrado: {document_path}")
            return False
        
        try:
            async def _send():
                with open(doc_file, 'rb') as doc:
                    return await self._bot.send_document(
                        chat_id=chat_id,
                        document=doc,
                        caption=caption
                    )
            
            self._run_async(_send())
            logger.info("[TelegramClient] Documento enviado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"[TelegramClient] Error enviando documento: {e}")
            return False
