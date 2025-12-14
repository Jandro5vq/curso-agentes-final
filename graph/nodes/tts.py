"""
TTS Node - Generación de audio con Coqui TTS
============================================

Este nodo genera audio a partir del guion usando el MCP de TTS.
Usa Coqui TTS como motor de síntesis de voz local.

Solo modifica el campo audio_path del estado.
"""

from typing import Any
import logging
import os
from datetime import datetime

from ..state import NewsState
from mcps import TTSClient


logger = logging.getLogger(__name__)

# Cliente TTS (singleton)
_tts_client: TTSClient | None = None


def get_tts_client() -> TTSClient:
    """Obtiene la instancia del cliente TTS."""
    global _tts_client
    if _tts_client is None:
        _tts_client = TTSClient()
    return _tts_client


def tts_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que genera audio a partir del guion.
    
    Usa Coqui TTS para sintetizar el texto del guion
    y guarda el archivo de audio resultante.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con la ruta del audio generado:
        {"audio_path": str | None}
    """
    script = state.get("script")
    chat_id = state["chat_id"]
    date = state["date"]
    mode = state["mode"]
    
    if not script:
        logger.warning("[TTS] No hay guion para sintetizar")
        return {"audio_path": None}
    
    logger.info(f"[TTS] Sintetizando audio para chat_id={chat_id}, mode={mode}")
    logger.info(f"[TTS] Longitud del guion: {len(script)} caracteres, {len(script.split())} palabras")
    
    # Generar nombre único para el archivo
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"podcast_{chat_id}_{date}_{mode}_{timestamp}.wav"
    
    client = get_tts_client()
    
    try:
        # Sintetizar audio
        audio_path = client.synthesize(
            text=script,
            output_filename=filename
        )
        
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            logger.info(f"[TTS] Audio generado: {audio_path} ({file_size / 1024:.1f} KB)")
            return {"audio_path": audio_path}
        else:
            logger.error(f"[TTS] El archivo de audio no se creó correctamente")
            return {"audio_path": None}
        
    except Exception as e:
        logger.error(f"[TTS] Error sintetizando audio: {e}")
        return {"audio_path": None}
