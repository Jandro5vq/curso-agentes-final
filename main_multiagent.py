"""
News Service - Main Entry Point (Multi-Agent Version)
======================================================

Este módulo es el punto de entrada para el servicio de noticias
usando la arquitectura multi-agente con tool calling real.

Arquitectura:
- OrchestratorAgent: Agente maestro que coordina
- ReporterAgent: Obtiene noticias (tools: fetch_news)
- WriterAgent: Genera guiones (LLM directo)
- ProducerAgent: Produce y envía (tools: TTS + Telegram)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Aplicar nest_asyncio ANTES de cualquier otra importación async
import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from graph.multiagent_graph import (
    get_multiagent_graph,
    create_initial_multiagent_state,
    print_graph_ascii,
    get_graph_mermaid,
)
from graph.multiagent_state import MultiAgentState
from persistence import StateStore
from scheduler import get_scheduler

from typing import Literal


# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("news_service.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

# Componentes globales
store = StateStore()
graph = None  # Se inicializa en main()


def get_today_date() -> str:
    """Retorna la fecha de hoy en formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


async def run_multiagent_graph(
    chat_id: int,
    mode: Literal["daily", "question", "mini_podcast"],
    user_input: str | None = None
) -> dict:
    """
    Ejecuta el grafo multi-agente para un chat.
    
    Args:
        chat_id: ID del chat de Telegram
        mode: Modo de operación
        user_input: Entrada del usuario
        
    Returns:
        Estado final después de la ejecución
    """
    global graph
    
    if graph is None:
        graph = get_multiagent_graph()
    
    date = get_today_date()
    
    # Guardar mensaje del usuario en conversation_history
    if user_input:
        store.add_conversation_message(
            chat_id=chat_id,
            date=date,
            role="user",
            content=user_input
        )
        logger.debug(f"[Main] Mensaje de usuario guardado en historial")
    
    # Crear estado inicial
    initial_state = create_initial_multiagent_state(
        chat_id=chat_id,
        date=date,
        mode=mode,
        user_input=user_input,
    )
    
    logger.info(f"[Main] Ejecutando grafo multi-agente: chat_id={chat_id}, mode={mode}")
    
    # Ejecutar el grafo
    try:
        config = {"configurable": {"thread_id": f"{chat_id}_{date}"}}
        final_state = await graph.ainvoke(initial_state, config)
        
        # Log del resultado
        agent_history = final_state.get("agent_history", [])
        tools_used = []
        for step in agent_history:
            tools_used.extend(step.get("tools_used", []))
        
        logger.info(f"[Main] Grafo completado. Success: {final_state.get('success')}")
        logger.info(f"[Main] Agentes ejecutados: {[s['agent'] for s in agent_history]}")
        logger.info(f"[Main] Tools invocadas por LLMs: {tools_used}")
        
        # Guardar respuesta del asistente en conversation_history
        assistant_content = None
        if mode == "question" and final_state.get("answer"):
            assistant_content = final_state.get("answer")
        elif mode in ("daily", "mini_podcast") and final_state.get("script"):
            assistant_content = f"[{mode.upper()}] {final_state.get('script')[:500]}..."
        
        if assistant_content:
            store.add_conversation_message(
                chat_id=chat_id,
                date=date,
                role="assistant",
                content=assistant_content
            )
            logger.debug(f"[Main] Respuesta del asistente guardada en historial")
        
        return final_state
        
    except Exception as e:
        logger.error(f"[Main] Error ejecutando grafo: {e}")
        raise


# =============================================================================
# HANDLERS DE TELEGRAM
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /start."""
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Usuario"
    
    logger.info(f"[Telegram] /start de chat_id={chat_id}")
    
    welcome_message = f"""
🎙️ *¡Bienvenido a La IA Dice, {user_name}!*

Tu podcast de noticias de tecnología e IA con *agentes inteligentes*:
• 🤖 *ReporterAgent* → Busca noticias
• ✍️ *WriterAgent* → Genera guiones
• 🎧 *ProducerAgent* → Produce y envía audio

*Comandos disponibles:*

📰 **/news** - Daily: Resumen diario de noticias mixtas (~3 min)

💊 **/podcast <tema>** - Píldora: Mini-podcast sobre un tema específico (~1 min)
   _Ejemplos:_
   • `/podcast inteligencia artificial`
   • `/podcast OpenAI`
   • `/podcast criptomonedas`

ℹ️ **/status** - Estado del sistema
📊 **/graph** - Ver arquitectura

También puedes *preguntarme sobre noticias* directamente.
    """
    
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /news - Genera podcast completo."""
    chat_id = update.effective_chat.id
    
    logger.info(f"[Telegram] /news de chat_id={chat_id}")
    
    wait_message = await update.message.reply_text(
        "🔄 *Iniciando sistema multi-agente...*\n\n"
        "1️⃣ ReporterAgent buscando noticias...\n"
        "2️⃣ WriterAgent generará el guion...\n"
        "3️⃣ ProducerAgent producirá el audio...",
        parse_mode="Markdown"
    )
    
    try:
        result = await run_multiagent_graph(chat_id, mode="daily")
        
        # Actualizar mensaje con resultado
        if result.get("success"):
            await wait_message.edit_text(
                "✅ *Podcast generado y enviado!*\n\n"
                f"📊 Agentes: {len(result.get('agent_history', []))} pasos\n"
                f"🔧 Tools usadas: {sum(len(s.get('tools_used', [])) for s in result.get('agent_history', []))}",
                parse_mode="Markdown"
            )
        else:
            await wait_message.edit_text(
                f"❌ Error: {result.get('error', 'Error desconocido')}"
            )
        
    except Exception as e:
        logger.error(f"[Telegram] Error en /news: {e}")
        await wait_message.edit_text(f"❌ Error: {str(e)}")


async def podcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /podcast <tema> - Genera una Píldora (mini-podcast temático)."""
    chat_id = update.effective_chat.id
    topic = " ".join(context.args) if context.args else None
    
    logger.info(f"[Telegram] /podcast de chat_id={chat_id}, topic={topic}")
    
    # El tema es obligatorio para las Píldoras
    if not topic:
        await update.message.reply_text(
            "💊 *Píldoras de La IA Dice*\n\n"
            "Las píldoras son mini-podcasts enfocados en un tema específico.\n\n"
            "📝 *Uso:* `/podcast <tema>`\n\n"
            "📌 *Ejemplos:*\n"
            "• `/podcast inteligencia artificial`\n"
            "• `/podcast OpenAI`\n"
            "• `/podcast criptomonedas`\n"
            "• `/podcast Tesla`\n"
            "• `/podcast startups españolas`",
            parse_mode="Markdown"
        )
        return
    
    wait_message = await update.message.reply_text(
        f"💊 Generando píldora sobre *{topic}*...",
        parse_mode="Markdown"
    )
    
    try:
        result = await run_multiagent_graph(
            chat_id, 
            mode="mini_podcast", 
            user_input=topic
        )
        
        if result.get("success"):
            await wait_message.edit_text(f"✅ Píldora sobre *{topic}* enviada!", parse_mode="Markdown")
        else:
            await wait_message.edit_text(f"❌ Error: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"[Telegram] Error en /podcast: {e}")
        await wait_message.edit_text(f"❌ Error: {str(e)}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /status."""
    chat_id = update.effective_chat.id
    
    logger.info(f"[Telegram] /status de chat_id={chat_id}")
    
    scheduler = get_scheduler()
    scheduler_status = scheduler.get_status()
    
    status_message = f"""
📊 *Estado del Sistema Multi-Agente*

🗓️ **Fecha**: {get_today_date()}

🤖 **Agentes disponibles**:
• OrchestratorAgent (Maestro)
• ReporterAgent (Tools: fetch\\_news)
• WriterAgent (LLM directo)
• ProducerAgent (Tools: TTS, Telegram)

🔧 **Tools MCP**:
• fetch\\_general\\_news\\_tool
• fetch\\_topic\\_news\\_tool
• synthesize\\_speech\\_tool
• send\\_telegram\\_message\\_tool
• send\\_telegram\\_audio\\_tool

⏰ **Scheduler**:
• Estado: {"🟢 Activo" if scheduler_status["running"] else "🔴 Inactivo"}
• Hora: {scheduler_status["daily_time"]}
• Próximo: {scheduler_status["next_run"] or "No programado"}
    """
    
    await update.message.reply_text(status_message, parse_mode="Markdown")


async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /graph - Muestra la arquitectura."""
    chat_id = update.effective_chat.id
    
    logger.info(f"[Telegram] /graph de chat_id={chat_id}")
    
    # Obtener mermaid del grafo
    try:
        mermaid_code = get_graph_mermaid()
        
        graph_message = f"""
📊 *Arquitectura Multi-Agente*

```
START
  │
  ▼
ROUTER
  │
  ▼
REPORTER 🤖
  │ Tools: fetch_news
  │
  ├──[daily/mini]──► WRITER 🤖
  │                    │ LLM
  │                    ▼
  │                 PRODUCER 🤖
  │                    │ Tools: TTS, Telegram
  │                    │
  └──[question]────► ANSWER 🤖
                       │
                       ▼
                   FINALIZE
                       │
                       ▼
                      END
```

🔗 *Mermaid*:
```
{mermaid_code[:500]}...
```
        """
        
        await update.message.reply_text(graph_message, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"Error generando grafo: {e}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para mensajes de texto (preguntas)."""
    chat_id = update.effective_chat.id
    user_message = update.message.text
    
    if not user_message or len(user_message.strip()) < 3:
        return
    
    logger.info(f"[Telegram] Mensaje de chat_id={chat_id}: '{user_message[:50]}...'")
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        result = await run_multiagent_graph(
            chat_id, 
            mode="question", 
            user_input=user_message
        )
        
        # La respuesta ya debería haber sido enviada por el ProducerAgent
        if not result.get("success"):
            await update.message.reply_text(
                f"❌ Error procesando pregunta: {result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"[Telegram] Error procesando mensaje: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def daily_news_callback(chat_id: int) -> None:
    """Callback para el scheduler."""
    logger.info(f"[Scheduler] Generando noticiario para chat_id={chat_id}")
    
    try:
        await run_multiagent_graph(chat_id, mode="daily")
    except Exception as e:
        logger.error(f"[Scheduler] Error: {e}")


def main() -> None:
    """Función principal."""
    global graph
    
    # Verificar configuración
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN no configurado")
        sys.exit(1)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("OPENAI_API_KEY no configurado")
        sys.exit(1)
    
    logger.info("=" * 70)
    logger.info("🎙️ SERVICIO DE NOTICIAS MULTI-AGENTE - INICIANDO")
    logger.info("=" * 70)
    
    # Mostrar arquitectura
    print_graph_ascii()
    
    # Crear directorio de audio
    Path("./audio").mkdir(exist_ok=True)
    
    # Inicializar grafo multi-agente
    logger.info("[Main] Inicializando grafo multi-agente...")
    graph = get_multiagent_graph()
    logger.info("[Main] Grafo inicializado con agentes y tools")
    
    # Inicializar scheduler
    scheduler = get_scheduler()
    scheduler.set_daily_callback(daily_news_callback)
    scheduler.start()
    
    logger.info(f"[Main] Scheduler iniciado. Próximo: {scheduler.get_next_run_time()}")
    
    # Crear aplicación de Telegram
    application = Application.builder().token(bot_token).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("podcast", podcast_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("graph", graph_command))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        message_handler
    ))
    
    logger.info("[Main] Bot de Telegram configurado")
    logger.info("[Main] Iniciando polling...")
    logger.info("=" * 70)
    
    # Iniciar bot
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("[Main] Deteniendo servicio...")
    finally:
        scheduler.stop()
        logger.info("[Main] Servicio detenido")


if __name__ == "__main__":
    main()
