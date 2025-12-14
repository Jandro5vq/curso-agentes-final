"""
Publish Node - Publicación en Telegram
======================================

Este nodo publica el resultado en Telegram usando el MCP de Telegram.

Dependiendo del modo y los datos disponibles:
- Si hay audio_path: envía el audio
- Si hay answer: envía el texto
- Si no hay ninguno: envía mensaje de error

Este nodo NO genera contenido, solo publica.
"""

from typing import Any
import logging

from ..state import NewsState
from mcps import TelegramClient


logger = logging.getLogger(__name__)

# Cliente Telegram (singleton)
_telegram_client: TelegramClient | None = None


def get_telegram_client() -> TelegramClient:
    """Obtiene la instancia del cliente Telegram."""
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


def publish_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que publica el resultado en Telegram.
    
    Publica:
    - Audio si existe (modos daily y mini_podcast)
    - Texto si hay respuesta (modo question)
    - Mensaje de error si no hay contenido
    
    Este nodo NO genera contenido, solo lo publica.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario vacío (no modifica el estado)
    """
    chat_id = state["chat_id"]
    mode = state["mode"]
    audio_path = state.get("audio_path")
    answer = state.get("answer")
    script = state.get("script")
    
    logger.info(f"[Publish] Publicando en chat_id={chat_id}, mode={mode}")
    
    client = get_telegram_client()
    
    try:
        # Caso 1: Hay audio (modos daily y mini_podcast)
        if audio_path:
            logger.info(f"[Publish] Enviando audio: {audio_path}")
            
            # Construir caption según el modo
            if mode == "daily":
                caption = "🎙️ *Noticiario del día*\n\n¡Aquí tienes las noticias más destacadas de hoy!"
            else:  # mini_podcast
                topic = state.get("user_input", "tema solicitado")
                caption = f"🎙️ *Mini-podcast*\n\nResumen sobre: _{topic}_"
            
            success = client.send_audio(
                chat_id=chat_id,
                audio_path=audio_path,
                caption=caption
            )
            
            if not success:
                # Fallback: enviar el guion como texto
                logger.warning("[Publish] Error enviando audio, intentando enviar guion como texto")
                if script:
                    client.send_text(
                        chat_id=chat_id,
                        text=f"📰 *Noticias del día*\n\n{script[:4000]}",
                        parse_mode="Markdown"
                    )
        
        # Caso 2: Hay respuesta textual (modo question)
        elif answer:
            logger.info(f"[Publish] Enviando respuesta de texto ({len(answer)} caracteres)")
            
            success = client.send_text(
                chat_id=chat_id,
                text=answer,
                parse_mode=None  # Sin formato para respuestas normales
            )
            
            if not success:
                logger.error("[Publish] Error enviando respuesta de texto")
        
        # Caso 3: No hay contenido para publicar
        else:
            logger.warning("[Publish] No hay contenido para publicar")
            client.send_text(
                chat_id=chat_id,
                text="Lo siento, no pude generar contenido en este momento. Por favor, inténtalo de nuevo más tarde.",
                parse_mode=None
            )
        
    except Exception as e:
        logger.error(f"[Publish] Error publicando: {e}")
        try:
            client.send_text(
                chat_id=chat_id,
                text="⚠️ Ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo más tarde.",
                parse_mode=None
            )
        except:
            pass
    
    # El nodo publish no modifica el estado
    return {}
