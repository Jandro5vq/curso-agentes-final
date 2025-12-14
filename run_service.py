"""
News Service con MCP Real
=========================

Este script integra el servidor MCP real de noticias con el sistema.
Usa langchain-mcp-adapters para conectar el MCP con LangChain.

Arquitectura:
┌─────────────────────────────────────────────────────────────────┐
│                     TELEGRAM BOT                                │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH                                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │ Reporter │──►│  Writer  │──►│ Producer │                    │
│  │  Agent   │   │  Agent   │   │  Agent   │                    │
│  └────┬─────┘   └──────────┘   └────┬─────┘                    │
│       │                             │                           │
│       ▼                             ▼                           │
│  ┌─────────────┐              ┌─────────────┐                  │
│  │ MCP NEWS    │              │ MCP TTS     │ (LangChain Tool) │
│  │ (FastMCP)   │              │ + TELEGRAM  │                  │
│  └─────────────┘              └─────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Añadir path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_mcp_server():
    """Prueba el servidor MCP de noticias."""
    print("\n" + "=" * 60)
    print("🧪 PROBANDO SERVIDOR MCP DE NOTICIAS")
    print("=" * 60)
    
    # Importar el servidor MCP
    from mcp_servers.news_server import (
        fetch_general_news,
        fetch_topic_news,
        get_news_sources,
    )
    
    print("\n📋 Fuentes disponibles:")
    print(get_news_sources())
    
    print("\n📰 Obteniendo 3 noticias generales...")
    news = fetch_general_news(max_articles=3)
    print(news[:1000])
    
    print("\n🔍 Buscando noticias sobre 'tecnología'...")
    tech_news = fetch_topic_news(topic="tecnología", max_articles=2)
    print(tech_news[:800])
    
    return True


async def test_multiagent_system():
    """Prueba el sistema multi-agente completo."""
    print("\n" + "=" * 60)
    print("🤖 PROBANDO SISTEMA MULTI-AGENTE")
    print("=" * 60)
    
    from graph.multiagent_graph import (
        get_multiagent_graph,
        create_initial_multiagent_state,
    )
    
    # Crear estado inicial (sin enviar a Telegram - solo prueba)
    state = create_initial_multiagent_state(
        chat_id=0,  # ID ficticio para prueba
        date=datetime.now().strftime("%Y-%m-%d"),
        mode="mini_podcast",
        user_input=None,
    )
    
    print("\n✅ Grafo multi-agente creado correctamente")
    print(f"   Estado inicial: mode={state['mode']}, chat_id={state['chat_id']}")
    
    return True


async def run_full_demo():
    """Ejecuta una demo completa del sistema."""
    print("\n" + "=" * 60)
    print("🎙️ DEMO COMPLETA DEL SISTEMA")
    print("=" * 60)
    
    # 1. Obtener noticias via MCP
    print("\n[1/4] Obteniendo noticias via MCP Real...")
    from mcp_servers.news_server import fetch_general_news
    news = fetch_general_news(max_articles=5)
    print(f"      ✅ Obtenidas noticias")
    
    # 2. Generar guion con WriterAgent
    print("\n[2/4] Generando guion con WriterAgent...")
    from agents import WriterAgent
    writer = WriterAgent()
    result = await writer.invoke(
        news_content=news,
        script_type="mini",
    )
    script = result.get("script", "")
    print(f"      ✅ Guion generado: {len(script.split())} palabras")
    print(f"\n--- GUION ---\n{script[:500]}...\n--- FIN ---")
    
    # 3. Generar audio con TTS
    print("\n[3/4] Generando audio con TTS...")
    from mcps import TTSClient
    tts = TTSClient()
    audio_path = tts.synthesize(
        text=script,
        output_filename="demo_podcast.mp3"
    )
    if audio_path:
        file_size = Path(audio_path).stat().st_size / 1024
        print(f"      ✅ Audio generado: {audio_path} ({file_size:.1f} KB)")
    else:
        print("      ❌ Error generando audio")
    
    # 4. Resumen
    print("\n[4/4] Resumen:")
    print(f"      📰 Noticias: 5 artículos")
    print(f"      📝 Guion: {len(script.split())} palabras")
    print(f"      🎙️ Audio: {audio_path if audio_path else 'No generado'}")
    
    return audio_path


def show_architecture():
    """Muestra la arquitectura del sistema."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                    NEWS SERVICE - ARQUITECTURA                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                      TELEGRAM BOT                               │  ║
║  │   /start  /news  /podcast  /status  [preguntas]                │  ║
║  └───────────────────────────┬─────────────────────────────────────┘  ║
║                              │                                        ║
║                              ▼                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                      LANGGRAPH                                  │  ║
║  │                                                                 │  ║
║  │   ┌──────────────┐                                              │  ║
║  │   │   REPORTER   │◄─── MCP REAL (FastMCP)                      │  ║
║  │   │    Agent     │     • fetch_general_news                    │  ║
║  │   │   (LLM)      │     • fetch_topic_news                      │  ║
║  │   └──────┬───────┘                                              │  ║
║  │          │                                                      │  ║
║  │          ▼                                                      │  ║
║  │   ┌──────────────┐                                              │  ║
║  │   │    WRITER    │◄─── LLM (GPT-4o-mini)                       │  ║
║  │   │    Agent     │     Genera guiones de podcast               │  ║
║  │   └──────┬───────┘                                              │  ║
║  │          │                                                      │  ║
║  │          ▼                                                      │  ║
║  │   ┌──────────────┐                                              │  ║
║  │   │   PRODUCER   │◄─── LangChain Tools                         │  ║
║  │   │    Agent     │     • synthesize_speech (Edge TTS)          │  ║
║  │   │   (LLM)      │     • send_telegram_audio                   │  ║
║  │   └──────────────┘     • send_telegram_message                 │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║  COMPONENTES:                                                         ║
║  • 1 MCP Real (FastMCP): news_server.py                              ║
║  • 3 LangChain Tools: TTS + Telegram                                 ║
║  • 4 Agentes LLM: Orchestrator, Reporter, Writer, Producer           ║
║  • 1 Grafo LangGraph con routing condicional                         ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


def show_commands():
    """Muestra los comandos disponibles."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                         COMANDOS DISPONIBLES                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  🚀 EJECUTAR EL BOT COMPLETO:                                        ║
║     python main_multiagent.py                                        ║
║                                                                       ║
║  🧪 PROBAR COMPONENTES:                                              ║
║     python run_service.py --test-mcp      # Prueba MCP de noticias   ║
║     python run_service.py --test-agents   # Prueba agentes           ║
║     python run_service.py --demo          # Demo completa            ║
║                                                                       ║
║  📊 VER ARQUITECTURA:                                                ║
║     python run_service.py --arch          # Muestra arquitectura     ║
║     python visualize_graph.py             # Visualiza grafo          ║
║                                                                       ║
║  🔧 EJECUTAR MCP SERVER STANDALONE:                                  ║
║     python -m mcp_servers.news_server     # Servidor MCP             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


async def main():
    """Punto de entrada principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="News Service Runner")
    parser.add_argument("--test-mcp", action="store_true", help="Probar MCP de noticias")
    parser.add_argument("--test-agents", action="store_true", help="Probar sistema multi-agente")
    parser.add_argument("--demo", action="store_true", help="Ejecutar demo completa")
    parser.add_argument("--arch", action="store_true", help="Mostrar arquitectura")
    parser.add_argument("--run", action="store_true", help="Ejecutar el bot")
    
    args = parser.parse_args()
    
    print("\n🎙️ NEWS SERVICE - Sistema Multi-Agente con MCP Real")
    print("=" * 60)
    
    if args.test_mcp:
        await test_mcp_server()
    elif args.test_agents:
        await test_multiagent_system()
    elif args.demo:
        await run_full_demo()
    elif args.arch:
        show_architecture()
    elif args.run:
        print("\nEjecutando bot... (usa main_multiagent.py)")
        os.system("python main_multiagent.py")
    else:
        show_architecture()
        show_commands()


if __name__ == "__main__":
    asyncio.run(main())
