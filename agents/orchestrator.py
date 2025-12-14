"""
Orchestrator Agent - Agente Maestro que coordina todo el sistema
================================================================

Este es el agente principal que:
1. Recibe las solicitudes del usuario
2. Decide qué sub-agentes invocar
3. Coordina el flujo entre agentes
4. Maneja errores y reintentos
"""

import os
import logging
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool

from .reporter import ReporterAgent
from .writer import WriterAgent
from .producer import ProducerAgent

logger = logging.getLogger(__name__)


ORCHESTRATOR_SYSTEM_PROMPT = """Eres el Director de un servicio de noticias por podcast.

Tu rol es coordinar un equipo de agentes especializados para producir podcasts de noticias.

## Tu equipo:
1. **Reporter**: Obtiene noticias de múltiples fuentes
2. **Writer**: Transforma noticias en guiones de podcast
3. **Producer**: Genera audio y lo envía por Telegram

## Flujos disponibles:

### DAILY (Podcast completo ~3min):
1. Pide al Reporter las noticias del día
2. Envía las noticias al Writer para crear guion completo
3. Envía el guion al Producer para generar y enviar audio

### MINI_PODCAST (Podcast corto ~1min):
1. Pide al Reporter las noticias principales
2. Envía al Writer para crear guion corto
3. Envía al Producer para producir y distribuir

### QUESTION (Respuesta textual):
1. Pide al Reporter noticias sobre el tema de la pregunta
2. Formula una respuesta basada en las noticias
3. Envía la respuesta por Telegram (sin audio)

## Instrucciones:
- Siempre sigue el flujo completo
- Si un agente falla, intenta una vez más
- Reporta el progreso de cada paso
- Al final, confirma si todo fue exitoso
"""


class OrchestratorAgent:
    """
    Agente Maestro que coordina los sub-agentes.
    
    Tiene acceso a herramientas que invocan a los sub-agentes:
    - delegate_to_reporter: Obtener noticias
    - delegate_to_writer: Generar guion
    - delegate_to_producer: Producir y enviar
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        """
        Inicializa el Orchestrator y sus sub-agentes.
        
        Args:
            model: Modelo de OpenAI a usar
            temperature: Temperatura para el orquestador
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Inicializar sub-agentes
        self.reporter = ReporterAgent(model=model)
        self.writer = WriterAgent(model=model)
        self.producer = ProducerAgent(model=model)
        
        logger.info("[OrchestratorAgent] Agente maestro inicializado con sub-agentes")
    
    async def process_request(
        self,
        mode: Literal["daily", "mini_podcast", "question"],
        chat_id: int,
        user_input: str | None = None
    ) -> dict[str, Any]:
        """
        Procesa una solicitud completa coordinando los sub-agentes.
        
        Args:
            mode: Tipo de solicitud (daily, mini_podcast, question)
            chat_id: ID del chat de Telegram
            user_input: Pregunta o tema del usuario (para question/mini_podcast)
        
        Returns:
            Diccionario con el resultado completo del procesamiento
        """
        logger.info(f"[Orchestrator] Procesando: mode={mode}, chat_id={chat_id}")
        
        result = {
            "mode": mode,
            "chat_id": chat_id,
            "steps": [],
            "success": False,
        }
        
        try:
            if mode == "daily":
                return await self._process_daily(chat_id, result)
            elif mode == "mini_podcast":
                return await self._process_mini_podcast(chat_id, user_input, result)
            elif mode == "question":
                return await self._process_question(chat_id, user_input, result)
            else:
                result["error"] = f"Modo no reconocido: {mode}"
                return result
                
        except Exception as e:
            logger.error(f"[Orchestrator] Error general: {e}")
            result["error"] = str(e)
            return result
    
    async def _process_daily(self, chat_id: int, result: dict) -> dict:
        """Flujo para podcast diario completo."""
        logger.info("[Orchestrator] Iniciando flujo DAILY")
        
        # Paso 1: Reporter obtiene noticias
        result["steps"].append({"step": "reporter", "status": "running"})
        reporter_task = "Obtén las 10 noticias más importantes del día en España. Incluye variedad de temas: política, economía, deportes, tecnología, sociedad."
        
        reporter_result = await self.reporter.invoke(reporter_task)
        result["steps"][-1]["status"] = "completed" if reporter_result["success"] else "failed"
        result["steps"][-1]["result"] = reporter_result
        
        if not reporter_result["success"]:
            result["error"] = "Reporter falló al obtener noticias"
            return result
        
        news_content = reporter_result["response"]
        
        # Paso 2: Writer genera guion
        result["steps"].append({"step": "writer", "status": "running"})
        
        writer_result = await self.writer.invoke(
            news_content=news_content,
            script_type="full",
            additional_instructions="Genera un podcast completo de ~3 minutos con todas las noticias."
        )
        result["steps"][-1]["status"] = "completed" if writer_result["success"] else "failed"
        result["steps"][-1]["result"] = writer_result
        
        if not writer_result["success"]:
            result["error"] = "Writer falló al generar guion"
            return result
        
        script = writer_result["script"]
        
        # Paso 3: Producer genera audio y envía
        result["steps"].append({"step": "producer", "status": "running"})
        
        producer_result = await self.producer.invoke(
            script=script,
            chat_id=chat_id,
            podcast_type="daily"
        )
        result["steps"][-1]["status"] = "completed" if producer_result["success"] else "failed"
        result["steps"][-1]["result"] = producer_result
        
        if not producer_result["success"]:
            result["error"] = "Producer falló al generar/enviar audio"
            return result
        
        result["success"] = True
        result["audio_path"] = producer_result.get("audio_path")
        logger.info("[Orchestrator] Flujo DAILY completado exitosamente")
        
        return result
    
    async def _process_mini_podcast(
        self, 
        chat_id: int, 
        topic: str | None,
        result: dict
    ) -> dict:
        """Flujo para mini-podcast (~1 min)."""
        logger.info(f"[Orchestrator] Iniciando flujo MINI_PODCAST: topic={topic}")
        
        # Paso 1: Reporter obtiene noticias
        result["steps"].append({"step": "reporter", "status": "running"})
        
        if topic:
            reporter_task = f"Busca las 5 noticias más importantes sobre: {topic}"
        else:
            reporter_task = "Obtén las 5 noticias más importantes y recientes de España."
        
        reporter_result = await self.reporter.invoke(reporter_task)
        result["steps"][-1]["status"] = "completed" if reporter_result["success"] else "failed"
        result["steps"][-1]["result"] = reporter_result
        
        if not reporter_result["success"]:
            result["error"] = "Reporter falló"
            return result
        
        news_content = reporter_result["response"]
        
        # Paso 2: Writer genera guion corto
        result["steps"].append({"step": "writer", "status": "running"})
        
        writer_result = await self.writer.invoke(
            news_content=news_content,
            script_type="mini",
            additional_instructions=f"Genera un mini-podcast de ~1 minuto. {'Enfócate en: ' + topic if topic else ''}"
        )
        result["steps"][-1]["status"] = "completed" if writer_result["success"] else "failed"
        result["steps"][-1]["result"] = writer_result
        
        if not writer_result["success"]:
            result["error"] = "Writer falló"
            return result
        
        script = writer_result["script"]
        
        # Paso 3: Producer
        result["steps"].append({"step": "producer", "status": "running"})
        
        producer_result = await self.producer.invoke(
            script=script,
            chat_id=chat_id,
            podcast_type="mini"
        )
        result["steps"][-1]["status"] = "completed" if producer_result["success"] else "failed"
        result["steps"][-1]["result"] = producer_result
        
        result["success"] = producer_result["success"]
        result["audio_path"] = producer_result.get("audio_path")
        
        return result
    
    async def _process_question(
        self, 
        chat_id: int, 
        question: str | None,
        result: dict
    ) -> dict:
        """Flujo para responder preguntas (sin audio)."""
        logger.info(f"[Orchestrator] Iniciando flujo QUESTION: {question}")
        
        if not question:
            result["error"] = "No se proporcionó una pregunta"
            return result
        
        # Paso 1: Reporter busca noticias relacionadas
        result["steps"].append({"step": "reporter", "status": "running"})
        reporter_task = f"Busca noticias relacionadas con esta pregunta del usuario: {question}"
        
        reporter_result = await self.reporter.invoke(reporter_task)
        result["steps"][-1]["status"] = "completed" if reporter_result["success"] else "failed"
        result["steps"][-1]["result"] = reporter_result
        
        news_content = reporter_result.get("response", "No se encontraron noticias relevantes.")
        
        # Paso 2: Generar respuesta (usando el LLM del orchestrator)
        result["steps"].append({"step": "answer_generation", "status": "running"})
        
        answer_prompt = f"""
Basándote en estas noticias, responde a la pregunta del usuario de forma clara y concisa.

PREGUNTA: {question}

NOTICIAS ENCONTRADAS:
{news_content}

Genera una respuesta informativa y útil. Si no hay noticias relevantes, indícalo amablemente.
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="Eres un asistente de noticias. Responde de forma clara y concisa basándote en la información proporcionada."),
                HumanMessage(content=answer_prompt)
            ])
            answer = response.content
            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["answer"] = answer
        except Exception as e:
            result["steps"][-1]["status"] = "failed"
            answer = f"Lo siento, hubo un error al procesar tu pregunta: {e}"
        
        # Paso 3: Enviar respuesta por Telegram
        result["steps"].append({"step": "producer_text", "status": "running"})
        
        producer_result = await self.producer.send_text_only(chat_id, answer)
        result["steps"][-1]["status"] = "completed" if producer_result["success"] else "failed"
        result["steps"][-1]["result"] = producer_result
        
        result["success"] = producer_result.get("success", False)
        result["answer"] = answer
        
        return result


def create_orchestrator_agent(
    model: str = "gpt-4o-mini",
    temperature: float = 0.3
) -> OrchestratorAgent:
    """Factory function para crear un OrchestratorAgent."""
    return OrchestratorAgent(model=model, temperature=temperature)
