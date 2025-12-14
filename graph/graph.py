"""
Grafo LangGraph para el servicio de noticias
============================================

Este módulo define el grafo de estados que implementa los 3 flujos:

1. daily: FetchGeneralNews → Writer → TTS → Publish
2. mini_podcast: FetchSpecificNews → Writer → TTS → Publish  
3. question: ContextEvaluator → (suficiente) → Answer → Publish
                             → (insuficiente) → FetchExtraInfo → Answer → Publish

El grafo usa add_conditional_edges para el routing condicional.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from .state import NewsState
from .nodes import (
    router_node,
    fetch_general_news_node,
    fetch_specific_news_node,
    writer_node,
    context_evaluator_node,
    fetch_extra_info_node,
    answer_from_memory_node,
    answer_with_augmentation_node,
    tts_node,
    publish_node,
)


def route_by_mode(state: NewsState) -> Literal["fetch_general_news", "fetch_specific_news", "context_evaluator"]:
    """
    Función de routing desde el nodo router.
    Determina el siguiente nodo basándose en el modo de operación.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Nombre del siguiente nodo a ejecutar
    """
    mode = state["mode"]
    
    if mode == "daily":
        return "fetch_general_news"
    elif mode == "mini_podcast":
        return "fetch_specific_news"
    elif mode == "question":
        return "context_evaluator"
    else:
        # Fallback seguro
        return "context_evaluator"


def route_by_context_evaluation(state: NewsState) -> Literal["answer_from_memory", "fetch_extra_info"]:
    """
    Función de routing desde el nodo context_evaluator.
    Determina si el contexto es suficiente para responder.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Nombre del siguiente nodo a ejecutar
    """
    if state.get("context_sufficient", False):
        return "answer_from_memory"
    else:
        return "fetch_extra_info"


def create_news_graph() -> StateGraph:
    """
    Crea y compila el grafo LangGraph para el servicio de noticias.
    
    El grafo implementa una máquina de estados con 3 flujos principales:
    
    - daily: Genera podcast diario de ~3 minutos con noticias generales
    - mini_podcast: Genera podcast corto de ~1 minuto sobre tema específico
    - question: Responde preguntas sobre las noticias del día
    
    Returns:
        Grafo compilado listo para ejecutar
    """
    # Crear el builder del grafo con el tipo de estado
    builder = StateGraph(NewsState)
    
    # =========================================================================
    # AGREGAR NODOS
    # =========================================================================
    
    # Nodo de entrada: Router
    builder.add_node("router", router_node)
    
    # Nodos de obtención de noticias
    builder.add_node("fetch_general_news", fetch_general_news_node)
    builder.add_node("fetch_specific_news", fetch_specific_news_node)
    
    # Nodo de generación de guion
    builder.add_node("writer", writer_node)
    
    # Nodos del flujo de preguntas
    builder.add_node("context_evaluator", context_evaluator_node)
    builder.add_node("fetch_extra_info", fetch_extra_info_node)
    builder.add_node("answer_from_memory", answer_from_memory_node)
    builder.add_node("answer_with_augmentation", answer_with_augmentation_node)
    
    # Nodo de generación de audio
    builder.add_node("tts", tts_node)
    
    # Nodo de publicación
    builder.add_node("publish", publish_node)
    
    # =========================================================================
    # DEFINIR ENTRY POINT
    # =========================================================================
    
    builder.add_edge(START, "router")
    
    # =========================================================================
    # EDGES CONDICIONALES DESDE ROUTER
    # =========================================================================
    
    builder.add_conditional_edges(
        source="router",
        path=route_by_mode,
        path_map={
            "fetch_general_news": "fetch_general_news",
            "fetch_specific_news": "fetch_specific_news",
            "context_evaluator": "context_evaluator",
        }
    )
    
    # =========================================================================
    # FLUJO DAILY: fetch_general_news → writer → tts → publish
    # =========================================================================
    
    builder.add_edge("fetch_general_news", "writer")
    
    # =========================================================================
    # FLUJO MINI_PODCAST: fetch_specific_news → writer → tts → publish
    # =========================================================================
    
    builder.add_edge("fetch_specific_news", "writer")
    
    # =========================================================================
    # FLUJO COMÚN PARA PODCASTS: writer → tts → publish
    # =========================================================================
    
    builder.add_edge("writer", "tts")
    builder.add_edge("tts", "publish")
    
    # =========================================================================
    # FLUJO QUESTION: context_evaluator → (condicional) → answer → publish
    # =========================================================================
    
    builder.add_conditional_edges(
        source="context_evaluator",
        path=route_by_context_evaluation,
        path_map={
            "answer_from_memory": "answer_from_memory",
            "fetch_extra_info": "fetch_extra_info",
        }
    )
    
    # Si contexto suficiente: answer_from_memory → publish
    builder.add_edge("answer_from_memory", "publish")
    
    # Si contexto insuficiente: fetch_extra_info → answer_with_augmentation → publish
    builder.add_edge("fetch_extra_info", "answer_with_augmentation")
    builder.add_edge("answer_with_augmentation", "publish")
    
    # =========================================================================
    # DEFINIR FINISH POINT
    # =========================================================================
    
    builder.add_edge("publish", END)
    
    # =========================================================================
    # COMPILAR Y RETORNAR
    # =========================================================================
    
    graph = builder.compile()
    
    return graph


# Instancia global del grafo para reutilización
_graph_instance: StateGraph | None = None


def get_news_graph() -> StateGraph:
    """
    Obtiene la instancia del grafo (singleton).
    
    Returns:
        Grafo compilado
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_news_graph()
    return _graph_instance
