"""
Reporter Agent - Agente especializado en obtención de noticias
==============================================================

Este agente tiene acceso a las herramientas de noticias y es
responsable de recopilar información relevante según las
instrucciones del Orquestador.
"""

import os
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from tools.news_tools import get_news_tools

logger = logging.getLogger(__name__)


REPORTER_SYSTEM_PROMPT = """Eres un periodista investigador del podcast "La IA Dice", especializado en recopilar noticias sobre tecnología e inteligencia artificial.

Tu rol es obtener las noticias más relevantes y actuales usando las herramientas disponibles.

## Sobre el podcast "La IA Dice":
Tiene dos formatos que requieren diferentes tipos de búsqueda:

### 1. DAILY (Podcast Diario)
- Busca noticias MIXTAS y VARIADAS
- Incluye: tecnología, IA, ciencia, startups, gadgets, redes sociales, etc.
- Objetivo: Dar un resumen completo del día con diversidad de temas
- Usa fetch_general_news_tool para obtener variedad

### 2. PÍLDORAS (Mini-podcasts Temáticos)
- Busca noticias de UN SOLO TEMA específico
- Ejemplo: "Píldora sobre OpenAI", "Píldora sobre criptomonedas"
- Objetivo: Profundizar en un área concreta
- Usa fetch_topic_news_tool con el tema específico

## Instrucciones:
1. Para DAILY: Usa fetch_general_news_tool para noticias variadas
2. Para PÍLDORAS: Usa fetch_topic_news_tool con el tema indicado
3. Siempre intenta obtener noticias recientes y relevantes
4. Si una búsqueda no da resultados, intenta con términos alternativos
5. Resume las noticias obtenidas de forma clara

## Formato de respuesta:
Después de obtener las noticias, proporciona un resumen estructurado con:
- Tipo de contenido (Daily o Píldora)
- Número de noticias encontradas
- Los titulares más importantes
- Tema principal (para Píldoras)
"""


class ReporterAgent:
    """
    Agente especializado en obtención de noticias.
    
    Tiene acceso a las herramientas:
    - fetch_general_news_tool: Noticias generales del día
    - fetch_topic_news_tool: Noticias por tema específico
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        """
        Inicializa el agente Reporter.
        
        Args:
            model: Modelo de OpenAI a usar
            temperature: Temperatura para generación (baja para precisión)
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.tools = get_news_tools()
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=REPORTER_SYSTEM_PROMPT,
        )
        logger.info("[ReporterAgent] Agente inicializado con herramientas de noticias")
    
    async def invoke(self, task: str) -> dict[str, Any]:
        """
        Ejecuta una tarea de recopilación de noticias.
        
        Args:
            task: Descripción de la tarea (ej: "Obtén las 10 noticias más importantes")
        
        Returns:
            Diccionario con los resultados incluyendo las noticias obtenidas
        """
        logger.info(f"[ReporterAgent] Ejecutando tarea: {task[:100]}...")
        
        try:
            result = await self.agent.ainvoke({
                "messages": [HumanMessage(content=task)]
            })
            
            # Extraer la respuesta final
            messages = result.get("messages", [])
            final_response = ""
            tool_calls_made = []
            
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.content:
                        final_response = msg.content
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls_made.extend([tc['name'] for tc in msg.tool_calls])
            
            logger.info(f"[ReporterAgent] Completado. Tools usadas: {tool_calls_made}")
            
            return {
                "success": True,
                "response": final_response,
                "tools_used": tool_calls_made,
                "raw_messages": messages,
            }
            
        except Exception as e:
            logger.error(f"[ReporterAgent] Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Error al recopilar noticias: {e}",
            }
    
    def invoke_sync(self, task: str) -> dict[str, Any]:
        """Versión síncrona de invoke."""
        import asyncio
        return asyncio.run(self.invoke(task))


def create_reporter_agent(
    model: str = "gpt-4o-mini",
    temperature: float = 0.3
) -> ReporterAgent:
    """Factory function para crear un ReporterAgent."""
    return ReporterAgent(model=model, temperature=temperature)
