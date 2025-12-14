"""
TTS Tools - Herramientas MCP para síntesis de voz
=================================================

Herramientas que encapsulan TTSClient para ser usadas
por agentes con tool calling.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from mcps import TTSClient

logger = logging.getLogger(__name__)

# Cliente singleton
_tts_client: Optional[TTSClient] = None


def _get_client() -> TTSClient:
    """Obtiene el cliente TTS singleton."""
    global _tts_client
    if _tts_client is None:
        _tts_client = TTSClient()
    return _tts_client


@tool
def synthesize_speech_tool(
    text: str,
    output_filename: str = ""
) -> str:
    """
    Convierte texto a audio (Text-to-Speech).
    
    Usa esta herramienta cuando necesites generar un archivo de audio
    a partir de un guion o texto. El audio se genera con una voz
    natural en español de España.
    
    Args:
        text: El texto completo que se convertirá en audio.
              Debe ser un guion preparado para locución.
        output_filename: Nombre opcional del archivo de salida (sin ruta).
                        Si no se especifica, se genera automáticamente.
    
    Returns:
        La ruta completa del archivo de audio generado (.mp3),
        o un mensaje de error si falla la síntesis.
    """
    logger.info(f"[Tool] synthesize_speech llamado: {len(text)} caracteres")
    
    if not text or not text.strip():
        return "Error: El texto para sintetizar no puede estar vacío."
    
    try:
        client = _get_client()
        
        # Generar nombre si no se proporcionó
        filename = output_filename if output_filename else None
        
        audio_path = client.synthesize(
            text=text,
            output_filename=filename
        )
        
        if audio_path:
            logger.info(f"[Tool] Audio generado exitosamente: {audio_path}")
            return f"✅ Audio generado exitosamente: {audio_path}"
        else:
            return "Error: No se pudo generar el archivo de audio."
            
    except Exception as e:
        logger.error(f"[Tool] Error en synthesize_speech: {e}")
        return f"Error al sintetizar audio: {str(e)}"


def get_tts_tools() -> list:
    """Retorna todas las herramientas de TTS."""
    return [synthesize_speech_tool]
