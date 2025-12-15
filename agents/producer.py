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

from tools.tts_tools import get_tts_tools, synthesize_speech_tool, synthesize_debate_multi_voice
from tools.telegram_tools import get_telegram_tools, send_telegram_audio_tool

logger = logging.getLogger(__name__)


PRODUCER_SYSTEM_PROMPT = """Eres el productor oficial de "La IA Dice", el podcast de noticias general que cubre todos los temas de actualidad.

Tu rol es convertir guiones de "La IA Dice" en audio y distribuirlos a los usuarios.

## Sobre el podcast "La IA Dice":
Tiene tres formatos:

### 1. DAILY (Podcast Diario)
- Resumen diario con noticias mixtas y variadas
- Caption: "🎙️ La IA Dice - Tu resumen diario de noticias"
- Usa: synthesize_speech_tool (una sola voz)

### 2. PÍLDORAS (Mini-podcasts Temáticos)  
- Contenido enfocado en un tema específico
- Caption: "💊 La IA Dice - Píldora: [TEMA]"
- Usa: synthesize_speech_tool (una sola voz)

### 3. DEBATE (Análisis Multi-Perspectiva)
- 4 voces diferentes debatiendo un tema
- Caption: "🎭 La IA Dice - Debate: [TEMA]"
- Usa: synthesize_debate_multi_voice (MÚLTIPLES VOCES)

## Tus capacidades:
1. Síntesis de voz simple: synthesize_speech_tool (para daily/píldora)
2. Síntesis multi-voz: synthesize_debate_multi_voice (para debates)
3. Distribución por Telegram: Enviar audio y mensajes a usuarios

## Proceso de producción:
1. Recibe el guion del Writer de "La IA Dice"
2. Según el tipo, usa la herramienta de TTS apropiada
3. Usa send_telegram_audio_tool para enviar al usuario
4. Confirma el envío exitoso

## Instrucciones importantes:
- Para DEBATES: SIEMPRE usa synthesize_debate_multi_voice (genera 4 voces diferentes)
- Para DAILY/PÍLDORA: usa synthesize_speech_tool
- Siempre genera el audio ANTES de intentar enviarlo
- Guarda la ruta del audio generado para el envío
- Si hay error en TTS, notifica al usuario por texto
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
            podcast_type: "daily", "pildora" o "debate"
            topic: Tema específico para las píldoras/debates
        
        Returns:
            Diccionario con el resultado de la producción
        """
        logger.info(f"[ProducerAgent] Produciendo {podcast_type} para chat_id={chat_id}")
        
        # Para debates, llamar directamente a las herramientas para garantizar multi-voz
        if podcast_type == "debate":
            return await self._produce_debate(script, chat_id, topic)
        
        # Para daily/pildora, usar el agente con LLM
        return await self._produce_standard(script, chat_id, podcast_type, topic)
    
    async def _produce_debate(
        self,
        script: str,
        chat_id: int,
        topic: str | None = None
    ) -> dict[str, Any]:
        """
        Produce un debate con múltiples voces llamando directamente a las herramientas.
        """
        topic_text = topic if topic else "tema de actualidad"
        caption = f"🎭 La IA Dice - Debate: {topic_text}"
        
        logger.info(f"[ProducerAgent] Generando debate multi-voz sobre: {topic_text}")
        
        try:
            # 1. Generar audio con múltiples voces
            tts_result = synthesize_debate_multi_voice.invoke({
                "script": script,
                "output_filename": f"debate_{topic_text.replace(' ', '_')[:20]}.mp3"
            })
            
            logger.info(f"[ProducerAgent] TTS Result: {tts_result}")
            
            if "Error" in tts_result:
                return {
                    "success": False,
                    "error": tts_result,
                    "response": f"Error generando audio del debate: {tts_result}",
                    "tools_used": ["synthesize_debate_multi_voice"],
                }
            
            # Extraer ruta del audio
            import re
            match = re.search(r'[\w./\\-]+\.mp3', tts_result)
            audio_path = match.group() if match else None
            
            if not audio_path:
                return {
                    "success": False,
                    "error": "No se pudo extraer la ruta del audio",
                    "response": tts_result,
                    "tools_used": ["synthesize_debate_multi_voice"],
                }
            
            # 2. Enviar por Telegram
            telegram_result = send_telegram_audio_tool.invoke({
                "chat_id": chat_id,
                "audio_path": audio_path,
                "caption": caption
            })
            
            logger.info(f"[ProducerAgent] Telegram Result: {telegram_result}")
            
            success = "enviado" in telegram_result.lower() or "éxito" in telegram_result.lower()
            
            return {
                "success": success,
                "response": f"Debate generado y enviado: {telegram_result}",
                "tools_used": ["synthesize_debate_multi_voice", "send_telegram_audio_tool"],
                "audio_path": audio_path,
                "chat_id": chat_id,
            }
            
        except Exception as e:
            logger.error(f"[ProducerAgent] Error en debate: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Error produciendo debate: {e}",
            }
    
    async def _produce_standard(
        self,
        script: str,
        chat_id: int,
        podcast_type: str = "daily",
        topic: str | None = None
    ) -> dict[str, Any]:
        """
        Produce un podcast estándar (daily/pildora) usando el agente LLM.
        """
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
