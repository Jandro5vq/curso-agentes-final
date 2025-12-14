"""
Tools - Herramientas MCP para LangChain
=======================================

Este módulo expone las herramientas que los agentes pueden invocar
mediante tool calling. Cada herramienta encapsula un cliente MCP.
"""

from .news_tools import (
    fetch_general_news_tool,
    fetch_topic_news_tool,
    get_news_tools,
)

from .tts_tools import (
    synthesize_speech_tool,
    get_tts_tools,
)

from .telegram_tools import (
    send_telegram_message_tool,
    send_telegram_audio_tool,
    get_telegram_tools,
)

__all__ = [
    # News tools
    "fetch_general_news_tool",
    "fetch_topic_news_tool",
    "get_news_tools",
    # TTS tools
    "synthesize_speech_tool",
    "get_tts_tools",
    # Telegram tools
    "send_telegram_message_tool",
    "send_telegram_audio_tool",
    "get_telegram_tools",
]
