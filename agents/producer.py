"""
Producer Agent - Agente especializado en producción y distribución
==================================================================

Este agente tiene acceso a las herramientas de TTS y Telegram,
y es responsable de producir el audio final y enviarlo al usuario.
"""

import os
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from tools.tts_tools import get_tts_tools
from tools.telegram_tools import get_telegram_tools

logger = logging.getLogger(__name__)


PRODUCER_SYSTEM_PROMPT = """Eres el productor oficial de "La IA Dice", el podcast de noticias general que cubre todos los temas de actualidad.

Tu rol es convertir guiones de "La IA Dice" en audio y distribuirlos a los usuarios.

## Sobre el podcast "La IA Dice":
Tiene dos formatos:

### 1. DAILY (Podcast Diario)
- Resumen diario con noticias mixtas y variadas
- Caption: "🎙️ La IA Dice - Tu resumen diario de noticias"

### 2. PÍLDORAS (Mini-podcasts Temáticos)  
- Contenido enfocado en un tema específico
- Caption: "💊 La IA Dice - Píldora: [TEMA]"

## Tus capacidades:
1. Síntesis de voz (TTS): Convertir texto a audio de alta calidad
2. Distribución por Telegram: Enviar audio y mensajes a usuarios

## Proceso de producción:
1. Recibe el guion del Writer de "La IA Dice"
2. Usa synthesize_speech_tool para generar el audio
3. Usa send_telegram_audio_tool para enviar al usuario
4. Confirma el envío exitoso

## Instrucciones importantes:
- Siempre genera el audio ANTES de intentar enviarlo
- Guarda la ruta del audio generado para el envío
- Usa el caption apropiado según el tipo (Daily o Píldora)
- Si hay error en TTS, notifica al usuario por texto
- Si hay error en Telegram, reporta el problema

## Captions:
- DAILY: "🎙️ La IA Dice - Tu resumen diario de noticias"
- PÍLDORA: "💊 La IA Dice - Píldora informativa"
"""


class ProducerAgent:
    """
    Agente especializado en producción de audio y distribución.
    
    Tiene acceso a las herramientas:
    - synthesize_speech_tool: Convertir texto a audio
    - send_telegram_message_tool: Enviar mensajes de texto
    - send_telegram_audio_tool: Enviar archivos de audio
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        """
        Inicializa el agente Producer.
        
        Args:
            model: Modelo de OpenAI a usar
            temperature: Temperatura baja para ejecución precisa
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        # Combinar herramientas de TTS y Telegram
        self.tools = get_tts_tools() + get_telegram_tools()
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=PRODUCER_SYSTEM_PROMPT,
        )
        logger.info("[ProducerAgent] Agente inicializado con herramientas de TTS y Telegram")
    
    async def invoke(
        self, 
        script: str, 
        chat_id: int,
        podcast_type: str = "daily",
        topic: str | None = None
    ) -> dict[str, Any]:
        """
        Produce y envía un podcast.
        
        Args:
            script: Guion a convertir en audio
            chat_id: ID del chat de Telegram
            podcast_type: "daily" (noticias mixtas) o "pildora" (temático)
            topic: Tema específico para las píldoras
        
        Returns:
            Diccionario con el resultado de la producción
        """
        logger.info(f"[ProducerAgent] Produciendo {podcast_type} para chat_id={chat_id}")
        
        # Construir caption según el tipo
        if podcast_type == "daily":
            caption = "🎙️ La IA Dice - Tu resumen diario de noticias"
        else:
            topic_text = topic if topic else "tecnología"
            caption = f"💊 La IA Dice - Píldora: {topic_text}"
        
        task = f"""
Necesito que produzcas y envíes un podcast:

1. PRIMERO: Usa synthesize_speech_tool para convertir este guion en audio:

---GUION---
{script}
---FIN GUION---

2. DESPUÉS: Una vez tengas la ruta del audio, usa send_telegram_audio_tool para enviarlo:
   - chat_id: {chat_id}
   - audio_path: (la ruta que obtuviste del paso 1)
   - caption: "{caption}"

3. Confirma que todo se completó correctamente.
"""
        
        try:
            result = await self.agent.ainvoke({
                "messages": [HumanMessage(content=task)]
            })
            
            messages = result.get("messages", [])
            final_response = ""
            tool_calls_made = []
            audio_path = None
            
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.content:
                        final_response = msg.content
                        # Intentar extraer la ruta del audio de la respuesta
                        if "audio/" in msg.content or ".mp3" in msg.content:
                            import re
                            match = re.search(r'[\w./\\]+\.mp3', msg.content)
                            if match:
                                audio_path = match.group()
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls_made.extend([tc['name'] for tc in msg.tool_calls])
            
            logger.info(f"[ProducerAgent] Completado. Tools usadas: {tool_calls_made}")
            
            return {
                "success": "Error" not in final_response,
                "response": final_response,
                "tools_used": tool_calls_made,
                "audio_path": audio_path,
                "chat_id": chat_id,
            }
            
        except Exception as e:
            logger.error(f"[ProducerAgent] Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Error en producción: {e}",
            }
    
    async def send_text_only(self, chat_id: int, message: str) -> dict[str, Any]:
        """
        Envía solo un mensaje de texto (para respuestas a preguntas).
        
        Usa directamente el cliente Telegram async para mayor fiabilidad.
        
        Args:
            chat_id: ID del chat de Telegram
            message: Mensaje a enviar
        
        Returns:
            Resultado del envío
        """
        logger.info(f"[ProducerAgent] Enviando texto directo a chat_id={chat_id}")
        
        try:
            # Usar directamente el cliente Telegram con método async
            from mcps import TelegramClient
            
            client = TelegramClient()
            success = await client.send_text_async(
                chat_id=chat_id,
                text=message
            )
            
            logger.info(f"[ProducerAgent] Resultado envío: success={success}")
            
            return {
                "success": success,
                "response": "Mensaje enviado" if success else "Error al enviar",
            }
            
        except Exception as e:
            logger.error(f"[ProducerAgent] Error enviando texto: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def invoke_sync(
        self, 
        script: str, 
        chat_id: int,
        podcast_type: str = "daily"
    ) -> dict[str, Any]:
        """Versión síncrona de invoke."""
        import asyncio
        return asyncio.run(self.invoke(script, chat_id, podcast_type))


def create_producer_agent(
    model: str = "gpt-4o-mini",
    temperature: float = 0.2
) -> ProducerAgent:
    """Factory function para crear un ProducerAgent."""
    return ProducerAgent(model=model, temperature=temperature)
