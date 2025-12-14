"""
Visualizar el grafo de LangGraph
================================

Script para generar y mostrar el grafo multi-agente.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from graph.multiagent_graph import (
    get_multiagent_graph,
    print_graph_ascii,
    get_graph_mermaid,
)


def main():
    print("\n" + "=" * 70)
    print("🎙️ VISUALIZACIÓN DEL GRAFO MULTI-AGENTE")
    print("=" * 70 + "\n")
    
    # Mostrar ASCII art
    print_graph_ascii()
    
    print("\n" + "=" * 70)
    print("📊 CÓDIGO MERMAID DEL GRAFO")
    print("=" * 70 + "\n")
    
    # Obtener y mostrar mermaid
    try:
        graph = get_multiagent_graph()
        mermaid = graph.get_graph().draw_mermaid()
        print(mermaid)
        
        # Guardar a archivo
        with open("graph_mermaid.md", "w") as f:
            f.write("```mermaid\n")
            f.write(mermaid)
            f.write("\n```\n")
        print("\n✅ Mermaid guardado en: graph_mermaid.md")
        
    except Exception as e:
        print(f"❌ Error generando mermaid: {e}")
    
    print("\n" + "=" * 70)
    print("📋 RESUMEN DE ARQUITECTURA")
    print("=" * 70 + "\n")
    
    print("""
┌─────────────────────────────────────────────────────────────────────┐
│                    SISTEMA MULTI-AGENTE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AGENTES (4 LLMs con roles especializados):                        │
│  ═══════════════════════════════════════════                        │
│                                                                     │
│  1. OrchestratorAgent (Maestro)                                    │
│     └── Coordina el flujo entre sub-agentes                        │
│     └── Decide qué agente invocar según el modo                    │
│                                                                     │
│  2. ReporterAgent (Sub-agente)                                     │
│     └── LLM: GPT-4o-mini con temperature=0.3                       │
│     └── Tools:                                                     │
│         ├── fetch_general_news_tool (NewsAPI/GNews/RSS)            │
│         └── fetch_topic_news_tool (búsqueda por tema)              │
│                                                                     │
│  3. WriterAgent (Sub-agente)                                       │
│     └── LLM: GPT-4o-mini con temperature=0.7                       │
│     └── Sin tools (generación directa de guiones)                  │
│                                                                     │
│  4. ProducerAgent (Sub-agente)                                     │
│     └── LLM: GPT-4o-mini con temperature=0.2                       │
│     └── Tools:                                                     │
│         ├── synthesize_speech_tool (Edge TTS)                      │
│         ├── send_telegram_message_tool                             │
│         └── send_telegram_audio_tool                               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TOOLS MCP (5 herramientas reales):                                │
│  ═══════════════════════════════════                                │
│                                                                     │
│  📰 News Tools (invocadas por ReporterAgent):                      │
│     ├── fetch_general_news_tool                                    │
│     │   └── Obtiene noticias generales de España                   │
│     │   └── Fuentes: NewsAPI → GNews → Google RSS                  │
│     │                                                               │
│     └── fetch_topic_news_tool                                      │
│         └── Busca noticias sobre un tema específico                │
│                                                                     │
│  🔊 TTS Tools (invocadas por ProducerAgent):                       │
│     └── synthesize_speech_tool                                     │
│         └── Convierte texto a audio con Edge TTS                   │
│         └── Voz: es-ES-AlvaroNeural                                │
│                                                                     │
│  📱 Telegram Tools (invocadas por ProducerAgent):                  │
│     ├── send_telegram_message_tool                                 │
│     │   └── Envía mensajes de texto                                │
│     │                                                               │
│     └── send_telegram_audio_tool                                   │
│         └── Envía archivos de audio                                │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FLUJOS DEL GRAFO:                                                 │
│  ══════════════════                                                 │
│                                                                     │
│  [daily/mini_podcast]:                                             │
│  START → Router → Reporter(tools) → Writer → Producer(tools) → END │
│                                                                     │
│  [question]:                                                       │
│  START → Router → Reporter(tools) → Answer(LLM+tool) → END         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
    """)


if __name__ == "__main__":
    main()
