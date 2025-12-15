"""
MultiAgentState - Estado para el sistema multi-agente
=====================================================

Estado tipado que fluye a través del grafo multi-agente.
Incluye información sobre el progreso de cada sub-agente.
"""

from typing import TypedDict, Literal, Any, Annotated
from operator import add


class AgentStep(TypedDict):
    """Representa un paso ejecutado por un agente."""
    agent: str  # reporter, writer, producer
    status: Literal["pending", "running", "completed", "failed"]
    input: str
    output: str | None
    tools_used: list[str]
    error: str | None


class MultiAgentState(TypedDict):
    """
    Estado compartido del sistema multi-agente.
    
    Este estado fluye a través de todos los nodos del grafo
    y mantiene el historial de ejecución de cada agente.
    """
    
    # Identificación
    chat_id: int
    date: str  # Formato: YYYY-MM-DD
    
    # Modo de operación
    mode: Literal["daily", "mini_podcast", "question", "debate"]
    user_input: str | None  # Pregunta del usuario o tema
    
    # Datos intermedios
    news_content: str | None  # Noticias obtenidas por Reporter
    perspectives: dict[str, str] | None  # Análisis desde múltiples perspectivas
    script: str | None  # Guion generado por Writer
    audio_path: str | None  # Ruta del audio generado
    answer: str | None  # Respuesta textual (modo question)
    
    # Seguimiento de ejecución
    current_agent: str | None  # Agente actualmente en ejecución
    agent_history: list[AgentStep]  # Historial de pasos
    
    # Estado final
    success: bool
    error: str | None
    
    # Metadatos
    metadata: dict[str, Any]


def create_initial_multiagent_state(
    chat_id: int,
    date: str,
    mode: Literal["daily", "mini_podcast", "question", "debate"],
    user_input: str | None = None,
) -> MultiAgentState:
    """
    Crea un estado inicial para el sistema multi-agente.
    
    Args:
        chat_id: ID del chat de Telegram
        date: Fecha en formato YYYY-MM-DD
        mode: Modo de operación
        user_input: Entrada del usuario (pregunta o tema)
    
    Returns:
        Estado inicial del sistema multi-agente
    """
    return MultiAgentState(
        chat_id=chat_id,
        date=date,
        mode=mode,
        user_input=user_input,
        news_content=None,
        perspectives=None,
        script=None,
        audio_path=None,
        answer=None,
        current_agent=None,
        agent_history=[],
        success=False,
        error=None,
        metadata={},
    )
