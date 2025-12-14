"""
Telegram Tools - Herramientas MCP para envío por Telegram
=========================================================

Herramientas que encapsulan TelegramClient para ser usadas
por agentes con tool calling.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from mcps import TelegramClient

logger = logging.getLogger(__name__)

# Cliente singleton
_telegram_client: Optional[TelegramClient] = None


def _get_client() -> TelegramClient:
    """Obtiene el cliente Telegram singleton."""
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


@tool
def send_telegram_message_tool(
    chat_id: int,
    message: str
) -> str:
    """
    Envía un mensaje de texto a un chat de Telegram.
    
    Usa esta herramienta cuando necesites enviar una respuesta
    textual al usuario en Telegram.
    
    Args:
        chat_id: El ID del chat de Telegram donde enviar el mensaje.
        message: El texto del mensaje a enviar. Puede incluir formato Markdown.
    
    Returns:
        Confirmación de envío exitoso o mensaje de error.
    """
    logger.info(f"[Tool] send_telegram_message llamado: chat_id={chat_id}")
    
    if not message or not message.strip():
        return "Error: El mensaje no puede estar vacío."
    
    try:
        client = _get_client()
        success = client.send_text(
            chat_id=chat_id,
            text=message
        )
        
        if success:
            logger.info(f"[Tool] Mensaje enviado a chat_id={chat_id}")
            return f"✅ Mensaje enviado correctamente al chat {chat_id}"
        else:
            return f"Error: No se pudo enviar el mensaje al chat {chat_id}"
            
    except Exception as e:
        logger.error(f"[Tool] Error en send_telegram_message: {e}")
        return f"Error al enviar mensaje: {str(e)}"


@tool
def send_telegram_audio_tool(
    chat_id: int,
    audio_path: str,
    caption: str = ""
) -> str:
    """
    Envía un archivo de audio a un chat de Telegram.
    
    Usa esta herramienta cuando necesites enviar un podcast o
    archivo de audio generado al usuario en Telegram.
    
    Args:
        chat_id: El ID del chat de Telegram donde enviar el audio.
        audio_path: Ruta completa al archivo de audio a enviar (.mp3 o .wav).
        caption: Texto opcional que acompaña al audio (ej: "🎙️ Tu podcast del día")
    
    Returns:
        Confirmación de envío exitoso o mensaje de error.
    """
    logger.info(f"[Tool] send_telegram_audio llamado: chat_id={chat_id}, audio={audio_path}")
    
    if not audio_path:
        return "Error: Debe especificar la ruta del archivo de audio."
    
    try:
        client = _get_client()
        success = client.send_audio(
            chat_id=chat_id,
            audio_path=audio_path,
            caption=caption
        )
        
        if success:
            logger.info(f"[Tool] Audio enviado a chat_id={chat_id}")
            return f"✅ Audio enviado correctamente al chat {chat_id}"
        else:
            return f"Error: No se pudo enviar el audio al chat {chat_id}"
            
    except Exception as e:
        logger.error(f"[Tool] Error en send_telegram_audio: {e}")
        return f"Error al enviar audio: {str(e)}"


def get_telegram_tools() -> list:
    """Retorna todas las herramientas de Telegram."""
    return [send_telegram_message_tool, send_telegram_audio_tool]
