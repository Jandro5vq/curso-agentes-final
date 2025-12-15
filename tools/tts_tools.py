"""
TTS Tools - Herramientas MCP para síntesis de voz
=================================================

Herramientas que encapsulan TTSClient para ser usadas
por agentes con tool calling.
"""

import logging
import re
import os
import asyncio
from pathlib import Path
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


# Mapeo de voces para el debate multi-perspectiva
DEBATE_VOICES = {
    "PRESENTADOR": "es-ES-AlvaroNeural",     # Voz masculina española (moderador)
    "PROGRESISTA": "es-ES-ElviraNeural",     # Voz femenina española
    "CONSERVADOR": "es-MX-JorgeNeural",      # Voz masculina mexicana
    "EXPERTO": "es-CO-GonzaloNeural",        # Voz masculina colombiana (diferente)
    "INTERNACIONAL": "es-AR-ElenaNeural",    # Voz femenina argentina
}


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


@tool
def synthesize_debate_multi_voice(
    script: str,
    output_filename: str = ""
) -> str:
    """
    Genera un audio de debate con múltiples voces diferentes.
    
    Esta herramienta procesa un guion con marcadores de sección como
    [PRESENTADOR], [PROGRESISTA], [CONSERVADOR], [EXPERTO], [INTERNACIONAL]
    y genera cada sección con una voz diferente, luego concatena todo.
    
    Args:
        script: Guion del debate con marcadores de sección [NOMBRE].
        output_filename: Nombre del archivo final (sin ruta).
    
    Returns:
        Ruta del archivo de audio final concatenado, o error.
    """
    logger.info(f"[Tool] synthesize_debate_multi_voice: {len(script)} caracteres")
    
    if not script or not script.strip():
        return "Error: El guion del debate no puede estar vacío."
    
    try:
        # Parsear las secciones del guion
        sections = _parse_debate_sections(script)
        
        if not sections:
            logger.warning("[Tool] No se encontraron marcadores de sección. Generando audio simple.")
            return synthesize_speech_tool.invoke({"text": script, "output_filename": output_filename})
        
        logger.info(f"[Tool] Encontradas {len(sections)} secciones de debate")
        
        # Generar audio para cada sección con su voz correspondiente
        audio_files = []
        output_dir = Path("./audio")
        output_dir.mkdir(exist_ok=True)
        
        import time
        timestamp = int(time.time())
        
        for i, (speaker, text) in enumerate(sections):
            if not text.strip():
                continue
                
            voice = DEBATE_VOICES.get(speaker, "es-ES-AlvaroNeural")
            section_filename = f"debate_{timestamp}_part{i:02d}_{speaker.lower()}.mp3"
            
            logger.info(f"[Tool] Generando sección {i+1}: {speaker} con voz {voice}")
            
            # Generar audio de la sección
            audio_path = _synthesize_with_voice(text, voice, output_dir / section_filename)
            
            if audio_path:
                audio_files.append(audio_path)
            else:
                logger.error(f"[Tool] Error generando sección {speaker}")
        
        if not audio_files:
            return "Error: No se pudieron generar los audios de las secciones."
        
        # Concatenar todos los audios
        final_filename = output_filename if output_filename else f"debate_{timestamp}_final.mp3"
        final_path = output_dir / final_filename
        
        success = _concatenate_audio_files(audio_files, str(final_path))
        
        if success:
            # Limpiar archivos temporales
            for temp_file in audio_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            logger.info(f"[Tool] Debate multi-voz generado: {final_path}")
            return f"✅ Audio de debate multi-voz generado: {final_path}"
        else:
            return "Error: No se pudo concatenar los audios del debate."
            
    except Exception as e:
        logger.error(f"[Tool] Error en synthesize_debate_multi_voice: {e}")
        return f"Error generando debate multi-voz: {str(e)}"


def _parse_debate_sections(script: str) -> list[tuple[str, str]]:
    """
    Parsea un guion de debate en secciones por speaker.
    
    Args:
        script: Guion con marcadores [SPEAKER]
        
    Returns:
        Lista de tuplas (speaker, texto)
    """
    # Patrón para encontrar marcadores de sección
    pattern = r'\[([A-ZÁÉÍÓÚÑ]+)\]'
    
    sections = []
    parts = re.split(pattern, script)
    
    # parts será: [texto_antes, SPEAKER1, texto1, SPEAKER2, texto2, ...]
    current_speaker = None
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
            
        # Si es un marcador de speaker conocido
        if part.upper() in DEBATE_VOICES:
            current_speaker = part.upper()
        elif current_speaker:
            # Es el texto de ese speaker
            sections.append((current_speaker, part))
    
    return sections


def _synthesize_with_voice(text: str, voice: str, output_path: Path) -> str | None:
    """
    Sintetiza texto con una voz específica de Edge TTS.
    
    Args:
        text: Texto a sintetizar
        voice: Nombre de la voz Edge TTS
        output_path: Ruta del archivo de salida
        
    Returns:
        Ruta del archivo generado o None si hay error
    """
    try:
        import edge_tts
        
        # Preprocesar texto
        processed_text = _preprocess_tts_text(text)
        
        async def _do_synthesis():
            communicate = edge_tts.Communicate(processed_text, voice)
            await communicate.save(str(output_path))
        
        # Ejecutar
        _run_async(_do_synthesis())
        
        if output_path.exists():
            return str(output_path)
        return None
        
    except Exception as e:
        logger.error(f"[Tool] Error sintetizando con voz {voice}: {e}")
        return None


def _concatenate_audio_files(audio_files: list[str], output_path: str) -> bool:
    """
    Concatena múltiples archivos de audio en uno solo.
    
    Intenta usar pydub si está disponible, sino usa método simple.
    """
    try:
        from pydub import AudioSegment
        
        combined = AudioSegment.empty()
        
        for audio_file in audio_files:
            segment = AudioSegment.from_mp3(audio_file)
            # Añadir pequeña pausa entre secciones (300ms)
            combined += segment + AudioSegment.silent(duration=300)
        
        combined.export(output_path, format="mp3")
        logger.info(f"[Tool] Audio concatenado con pydub: {output_path}")
        return True
        
    except ImportError:
        logger.warning("[Tool] pydub no disponible, usando método alternativo")
        return _concatenate_simple(audio_files, output_path)
    except Exception as e:
        logger.error(f"[Tool] Error concatenando con pydub: {e}")
        return _concatenate_simple(audio_files, output_path)


def _concatenate_simple(audio_files: list[str], output_path: str) -> bool:
    """
    Método simple de concatenación (copia binaria).
    Funciona pero puede tener pequeños glitches.
    """
    try:
        with open(output_path, 'wb') as outfile:
            for audio_file in audio_files:
                with open(audio_file, 'rb') as infile:
                    outfile.write(infile.read())
        return True
    except Exception as e:
        logger.error(f"[Tool] Error en concatenación simple: {e}")
        return False


def _preprocess_tts_text(text: str) -> str:
    """Preprocesa texto para TTS."""
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text)
    
    # Eliminar caracteres problemáticos
    text = text.replace('*', '')
    text = text.replace('_', ' ')
    text = text.replace('#', '')
    text = text.replace('`', '')
    
    # Normalizar comillas
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text.strip()


def _run_async(coro):
    """Ejecuta una coroutine de forma síncrona."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def get_tts_tools() -> list:
    """Retorna todas las herramientas de TTS."""
    return [synthesize_speech_tool, synthesize_debate_multi_voice]
