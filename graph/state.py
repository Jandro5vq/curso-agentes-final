"""
NewsState - Estado compartido del grafo LangGraph
================================================

Este módulo define el estado tipado que fluye a través de todos los nodos
del grafo. Cada nodo solo modifica los campos que le corresponden.

Campos:
    - chat_id: Identificador del chat de Telegram
    - date: Fecha del estado (YYYY-MM-DD)
    - mode: Modo de operación (daily, question, mini_podcast)
    - user_input: Entrada del usuario (pregunta o tema para mini-podcast)
    - articles: Lista de artículos de noticias obtenidos
    - script: Guion generado para el podcast
    - context_sufficient: Indica si el contexto es suficiente para responder
    - external_articles: Artículos adicionales buscados si contexto insuficiente
    - answer: Respuesta textual generada
    - audio_path: Ruta del archivo de audio generado
    - conversation: Historial de conversación del día
"""

from typing import TypedDict, Literal


class NewsState(TypedDict):
    """
    Estado compartido del grafo LangGraph para el servicio de noticias.
    
    Este estado se persiste diariamente por chat_id en SQLite y fluye
    a través de todos los nodos del grafo.
    """
    
    # Identificación
    chat_id: int
    date: str  # Formato: YYYY-MM-DD
    
    # Modo de operación
    mode: Literal["daily", "question", "mini_podcast"]
    user_input: str | None  # Pregunta del usuario o tema para mini-podcast
    
    # Datos de noticias
    articles: list[dict]  # Artículos obtenidos del MCP de noticias
    script: str | None  # Guion generado para locución
    
    # Evaluación de contexto (solo para modo question)
    context_sufficient: bool | None
    external_articles: list[dict] | None  # Info adicional si contexto insuficiente
    
    # Salidas
    answer: str | None  # Respuesta textual (modo question)
    audio_path: str | None  # Ruta del audio generado (modos daily y mini_podcast)
    
    # Historial
    conversation: list[dict]  # Formato: [{"role": "user"|"assistant", "content": str}]


def create_initial_state(
    chat_id: int,
    date: str,
    mode: Literal["daily", "question", "mini_podcast"],
    user_input: str | None = None,
    existing_articles: list[dict] | None = None,
    existing_conversation: list[dict] | None = None,
) -> NewsState:
    """
    Crea un estado inicial para una nueva ejecución del grafo.
    
    Args:
        chat_id: ID del chat de Telegram
        date: Fecha en formato YYYY-MM-DD
        mode: Modo de operación
        user_input: Entrada del usuario (requerido para question y mini_podcast)
        existing_articles: Artículos previos del día (para mantener contexto)
        existing_conversation: Conversación previa del día
    
    Returns:
        NewsState inicializado con valores por defecto
    """
    return NewsState(
        chat_id=chat_id,
        date=date,
        mode=mode,
        user_input=user_input,
        articles=existing_articles or [],
        script=None,
        context_sufficient=None,
        external_articles=None,
        answer=None,
        audio_path=None,
        conversation=existing_conversation or [],
    )


def merge_state_for_persistence(
    existing_state: NewsState | None,
    new_state: NewsState,
) -> NewsState:
    """
    Combina el estado existente con el nuevo estado tras una ejecución.
    
    Mantiene el historial de conversación y artículos acumulados del día.
    
    Args:
        existing_state: Estado previo del día (puede ser None)
        new_state: Estado resultante de la última ejecución
    
    Returns:
        Estado combinado para persistir
    """
    if existing_state is None:
        return new_state
    
    # Combinar artículos sin duplicados (por título)
    existing_titles = {a.get("title") for a in existing_state.get("articles", [])}
    combined_articles = list(existing_state.get("articles", []))
    for article in new_state.get("articles", []):
        if article.get("title") not in existing_titles:
            combined_articles.append(article)
            existing_titles.add(article.get("title"))
    
    # Combinar artículos externos
    combined_external = list(existing_state.get("external_articles") or [])
    new_external = new_state.get("external_articles") or []
    if new_external:
        external_titles = {a.get("title") for a in combined_external}
        for article in new_external:
            if article.get("title") not in external_titles:
                combined_external.append(article)
    
    # El nuevo estado hereda lo combinado
    merged = NewsState(
        chat_id=new_state["chat_id"],
        date=new_state["date"],
        mode=new_state["mode"],
        user_input=new_state["user_input"],
        articles=combined_articles,
        script=new_state.get("script") or existing_state.get("script"),
        context_sufficient=new_state.get("context_sufficient"),
        external_articles=combined_external if combined_external else None,
        answer=new_state.get("answer"),
        audio_path=new_state.get("audio_path"),
        conversation=new_state.get("conversation", []),
    )
    
    return merged
