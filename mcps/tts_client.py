"""
MCP TTS Client - Cliente para síntesis de voz
==============================================

Este módulo implementa el cliente MCP de TTS que proporciona:

- synthesize(text, output_filename): Genera audio a partir de texto

Soporta dos backends:
1. Edge TTS (Microsoft) - Por defecto, no requiere instalación especial
2. Coqui TTS - Opcional, requiere Python < 3.12 y Visual C++ Build Tools
"""

import os
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class TTSClient:
    """
    Cliente MCP para síntesis de voz.
    
    Por defecto usa Edge TTS (Microsoft) que no requiere instalación especial.
    Opcionalmente puede usar Coqui TTS para mayor calidad local.
    """
    
    # Voces de Edge TTS en español
    EDGE_VOICES = {
        "es-ES": "es-ES-AlvaroNeural",      # España - Masculino
        "es-ES-f": "es-ES-ElviraNeural",    # España - Femenino
        "es-MX": "es-MX-JorgeNeural",       # México - Masculino
        "es-MX-f": "es-MX-DaliaNeural",     # México - Femenino
        "es-AR": "es-AR-TomasNeural",       # Argentina - Masculino
    }
    
    def __init__(
        self, 
        backend: str | None = None,
        model_name: str | None = None, 
        output_dir: str | None = None,
        voice: str | None = None
    ):
        """
        Inicializa el cliente TTS.
        
        Args:
            backend: 'edge' o 'coqui'. Por defecto 'edge'.
            model_name: Nombre del modelo Coqui TTS (solo si backend='coqui')
            output_dir: Directorio para guardar los archivos de audio.
            voice: Voz a usar (para Edge TTS: código de idioma como 'es-ES')
        """
        self.backend = backend or os.getenv("TTS_BACKEND", "edge")
        self.model_name = model_name or os.getenv(
            "TTS_MODEL", 
            "tts_models/es/css10/vits"
        )
        self.output_dir = Path(output_dir or os.getenv("TTS_OUTPUT_DIR", "./audio"))
        self.voice = voice or os.getenv("TTS_VOICE", "es-ES")
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Para Coqui TTS (carga lazy)
        self._coqui_tts = None
        self._initialized = False
        
        logger.info(f"[TTSClient] Backend: {self.backend}, Voice: {self.voice}")
    
    def synthesize(
        self,
        text: str,
        output_filename: str | None = None
    ) -> str | None:
        """
        Sintetiza texto a audio.
        
        Args:
            text: Texto a convertir en audio
            output_filename: Nombre del archivo de salida (sin ruta).
        
        Returns:
            Ruta completa del archivo de audio generado, o None si hay error
        """
        if not text or not text.strip():
            logger.warning("[TTSClient] Texto vacío para sintetizar")
            return None
        
        # Generar nombre de archivo si no se proporcionó
        if not output_filename:
            import time
            output_filename = f"tts_{int(time.time())}.mp3"
        
        # Asegurar extensión correcta según backend
        if self.backend == "edge" and not output_filename.endswith(".mp3"):
            output_filename = output_filename.rsplit(".", 1)[0] + ".mp3"
        elif self.backend == "coqui" and not output_filename.endswith(".wav"):
            output_filename = output_filename.rsplit(".", 1)[0] + ".wav"
        
        output_path = self.output_dir / output_filename
        
        logger.info(f"[TTSClient] Sintetizando {len(text)} caracteres -> {output_path}")
        
        if self.backend == "edge":
            return self._synthesize_edge(text, output_path)
        elif self.backend == "coqui":
            return self._synthesize_coqui(text, output_path)
        else:
            logger.error(f"[TTSClient] Backend no soportado: {self.backend}")
            return None
    
    def _synthesize_edge(self, text: str, output_path: Path) -> str | None:
        """Sintetiza usando Edge TTS (Microsoft)."""
        try:
            import edge_tts
            
            # Obtener voz
            voice = self.EDGE_VOICES.get(self.voice, self.voice)
            if self.voice not in self.EDGE_VOICES and not self.voice.endswith("Neural"):
                voice = self.EDGE_VOICES.get("es-ES")  # Fallback
            
            logger.info(f"[TTSClient] Usando Edge TTS con voz: {voice}")
            
            # Preprocesar texto
            processed_text = self._preprocess_text(text)
            
            # Edge TTS es async, ejecutar en event loop
            async def _do_synthesis():
                communicate = edge_tts.Communicate(processed_text, voice)
                await communicate.save(str(output_path))
            
            # Ejecutar async
            self._run_async(_do_synthesis())
            
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"[TTSClient] Audio generado: {output_path} ({file_size / 1024:.1f} KB)")
                return str(output_path)
            else:
                logger.error("[TTSClient] El archivo de audio no se creó")
                return None
                
        except ImportError:
            logger.error("[TTSClient] edge-tts no está instalado")
            logger.error("[TTSClient] Instala con: pip install edge-tts")
            return None
        except Exception as e:
            logger.error(f"[TTSClient] Error con Edge TTS: {e}")
            return None
    
    def _synthesize_coqui(self, text: str, output_path: Path) -> str | None:
        """Sintetiza usando Coqui TTS."""
        if not self._ensure_coqui_initialized():
            return None
        
        try:
            processed_text = self._preprocess_text(text)
            
            self._coqui_tts.tts_to_file(
                text=processed_text,
                file_path=str(output_path)
            )
            
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"[TTSClient] Audio generado: {output_path} ({file_size / 1024:.1f} KB)")
                return str(output_path)
            else:
                logger.error("[TTSClient] El archivo de audio no se creó")
                return None
                
        except Exception as e:
            logger.error(f"[TTSClient] Error con Coqui TTS: {e}")
            return None
    
    def _ensure_coqui_initialized(self) -> bool:
        """Inicializa Coqui TTS si es necesario."""
        if self._initialized:
            return True
        
        try:
            logger.info(f"[TTSClient] Cargando modelo Coqui TTS: {self.model_name}")
            
            from TTS.api import TTS
            import torch
            
            use_gpu = os.getenv("TTS_USE_GPU", "true").lower() == "true"
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            
            logger.info(f"[TTSClient] Usando dispositivo: {device}")
            
            self._coqui_tts = TTS(model_name=self.model_name, progress_bar=False)
            self._coqui_tts.to(device)
            
            self._initialized = True
            logger.info("[TTSClient] Modelo Coqui TTS cargado correctamente")
            return True
            
        except ImportError as e:
            logger.error(f"[TTSClient] Coqui TTS no está instalado: {e}")
            return False
        except Exception as e:
            logger.error(f"[TTSClient] Error cargando Coqui TTS: {e}")
            return False
    
    def _run_async(self, coro):
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
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocesa el texto para mejorar la síntesis.
        
        - Normaliza espacios
        - Elimina caracteres problemáticos
        - Añade pausas en puntos apropiados
        """
        import re
        
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar caracteres especiales problemáticos
        text = text.replace('*', '')
        text = text.replace('_', ' ')
        text = text.replace('#', '')
        text = text.replace('`', '')
        
        # Normalizar comillas
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Añadir pausa después de dos puntos (para enumeraciones)
        text = text.replace(':', ':,')
        
        # Asegurar espacio después de puntuación
        text = re.sub(r'([.!?])([A-ZÁÉÍÓÚÑ])', r'\1 \2', text)
        
        return text.strip()
    
    def list_edge_voices(self) -> list[str]:
        """Lista las voces disponibles de Edge TTS."""
        return list(self.EDGE_VOICES.keys())
    
    def get_info(self) -> dict:
        """Obtiene información del cliente TTS."""
        return {
            "backend": self.backend,
            "voice": self.voice,
            "output_dir": str(self.output_dir),
            "coqui_model": self.model_name if self.backend == "coqui" else None,
            "coqui_initialized": self._initialized,
        }
