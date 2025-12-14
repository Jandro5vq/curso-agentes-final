"""
Router Node - Nodo de enrutamiento inicial
==========================================

Este nodo es el punto de entrada del grafo. Su única función es
validar el estado y prepararlo para el routing condicional.

No modifica el modo, solo valida que esté correctamente configurado.
El routing real lo hace la función route_by_mode en graph.py.
"""

from typing import Any
from ..state import NewsState


def router_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo router: punto de entrada del grafo.
    
    Valida el estado de entrada y lo prepara para el routing.
    No modifica el modo - el routing condicional se hace en graph.py.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con actualizaciones mínimas al estado (vacío si todo OK)
        
    Raises:
        ValueError: Si el modo no es válido
    """
    mode = state.get("mode")
    
    # Validar que el modo sea válido
    valid_modes = {"daily", "question", "mini_podcast"}
    if mode not in valid_modes:
        raise ValueError(
            f"Modo inválido: {mode}. "
            f"Modos válidos: {valid_modes}"
        )
    
    # Validar que user_input esté presente para modos que lo requieren
    if mode in ("question", "mini_podcast") and not state.get("user_input"):
        raise ValueError(
            f"El modo '{mode}' requiere user_input pero está vacío"
        )
    
    # Validar chat_id
    if not state.get("chat_id"):
        raise ValueError("chat_id es requerido")
    
    # Validar date
    if not state.get("date"):
        raise ValueError("date es requerido")
    
    # El router no modifica el estado, solo valida
    # El routing real lo hace route_by_mode como conditional edge
    return {}
