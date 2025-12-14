"""
News Service - Main Entry Point
================================

Este módulo es el punto de entrada principal del servicio de noticias.

Implementa:
- Bot de Telegram con handlers para comandos y mensajes
- Integración con el grafo LangGraph
- Persistencia de estado con SQLite
- Scheduler para noticiario diario

Comandos de Telegram:
- /start: Inicia el bot y suscribe al chat
- /news: Genera el noticiario del día bajo demanda
- /podcast <tema>: Genera mini-podcast sobre un tema
- /status: Muestra el estado del servicio
- Mensajes de texto: Preguntas sobre las noticias del día
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

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

from graph import NewsState, create_news_graph
from graph.state import create_initial_state, merge_state_for_persistence
from persistence import StateStore
from scheduler import get_scheduler

from typing import Literal, cast


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
graph = create_news_graph()


def get_today_date() -> str:
    """Retorna la fecha de hoy en formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


async def run_graph_for_chat(
    chat_id: int,
    mode: Literal["daily", "question", "mini_podcast"],
    user_input: str | None = None
) -> dict:
    """
    Ejecuta el grafo LangGraph para un chat.
    
    Args:
        chat_id: ID del chat de Telegram
        mode: Modo de operación ('daily', 'question', 'mini_podcast')
        user_input: Entrada del usuario (requerido para question y mini_podcast)
        
    Returns:
        Estado final después de la ejecución
    """
    date = get_today_date()
    
    # Cargar estado existente del día
    existing_state = store.load_state(chat_id, date)
    
    # Crear estado inicial para esta ejecución
    initial_state = create_initial_state(
        chat_id=chat_id,
        date=date,
        mode=mode,
        user_input=user_input,
        existing_articles=existing_state.get("articles") if existing_state else None,
        existing_conversation=existing_state.get("conversation") if existing_state else None,
    )
    
    logger.info(f"[Main] Ejecutando grafo: chat_id={chat_id}, mode={mode}")
    
    # Ejecutar el grafo
    try:
        final_state = graph.invoke(initial_state)
        
        # Combinar con estado existente y guardar
        merged_state = merge_state_for_persistence(
            cast(NewsState, existing_state) if existing_state else None, 
            cast(NewsState, final_state)
        )
        store.save_state(chat_id, date, dict(merged_state))
        
        logger.info(f"[Main] Grafo ejecutado exitosamente para chat_id={chat_id}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"[Main] Error ejecutando grafo: {e}")
        raise


# =============================================================================
# HANDLERS DE TELEGRAM
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para el comando /start.
    Presenta el bot y suscribe al chat para el noticiario diario.
    """
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Usuario"
    
    logger.info(f"[Telegram] /start de chat_id={chat_id}")
    
    # Crear estado inicial para el chat (lo suscribe implícitamente)
    date = get_today_date()
    initial_state = create_initial_state(
        chat_id=chat_id,
        date=date,
        mode="daily",
        user_input=None,
    )
    store.save_state(chat_id, date, dict(initial_state))
    
    welcome_message = f"""
🎙️ *¡Bienvenido al Servicio de Noticias, {user_name}!*

Puedo ayudarte con:

📰 **/news** - Genera el noticiario del día (~3 minutos)
🎧 **/podcast <tema>** - Mini-podcast sobre un tema específico (~1 minuto)
ℹ️ **/status** - Estado del servicio

También puedes *escribirme directamente* para preguntarme sobre las noticias del día.

_El noticiario diario se genera automáticamente cada mañana._
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown"
    )


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para el comando /news.
    Genera el noticiario diario bajo demanda.
    """
    chat_id = update.effective_chat.id
    
    logger.info(f"[Telegram] /news de chat_id={chat_id}")
    
    # Enviar mensaje de espera
    wait_message = await update.message.reply_text(
        "🔄 Generando tu noticiario del día...\n\n"
        "_Esto puede tardar unos segundos mientras busco las noticias y genero el audio._",
        parse_mode="Markdown"
    )
    
    try:
        # Ejecutar el grafo en modo daily
        await run_graph_for_chat(chat_id, mode="daily")
        
        # Eliminar mensaje de espera
        await wait_message.delete()
        
    except Exception as e:
        logger.error(f"[Telegram] Error en /news: {e}")
        await wait_message.edit_text(
            "❌ Ha ocurrido un error generando el noticiario. "
            "Por favor, inténtalo de nuevo más tarde."
        )


async def podcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para el comando /podcast <tema>.
    Genera un mini-podcast sobre el tema especificado.
    """
    chat_id = update.effective_chat.id
    
    # Extraer el tema del comando
    if context.args:
        topic = " ".join(context.args)
    else:
        await update.message.reply_text(
            "❓ Por favor, especifica un tema.\n\n"
            "Ejemplo: `/podcast inteligencia artificial`",
            parse_mode="Markdown"
        )
        return
    
    logger.info(f"[Telegram] /podcast '{topic}' de chat_id={chat_id}")
    
    # Enviar mensaje de espera
    wait_message = await update.message.reply_text(
        f"🔄 Generando mini-podcast sobre *{topic}*...\n\n"
        "_Buscando noticias y generando audio._",
        parse_mode="Markdown"
    )
    
    try:
        # Ejecutar el grafo en modo mini_podcast
        await run_graph_for_chat(chat_id, mode="mini_podcast", user_input=topic)
        
        # Eliminar mensaje de espera
        await wait_message.delete()
        
    except Exception as e:
        logger.error(f"[Telegram] Error en /podcast: {e}")
        await wait_message.edit_text(
            "❌ Ha ocurrido un error generando el podcast. "
            "Por favor, inténtalo de nuevo más tarde."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para el comando /status.
    Muestra el estado del servicio.
    """
    chat_id = update.effective_chat.id
    
    logger.info(f"[Telegram] /status de chat_id={chat_id}")
    
    # Obtener estadísticas
    db_stats = store.get_stats()
    scheduler = get_scheduler()
    scheduler_status = scheduler.get_status()
    
    # Obtener estado del chat actual
    date = get_today_date()
    chat_state = store.load_state(chat_id, date)
    
    articles_count = len(chat_state.get("articles", [])) if chat_state else 0
    messages_count = len(chat_state.get("conversation", [])) if chat_state else 0
    
    status_message = f"""
📊 *Estado del Servicio de Noticias*

🗓️ **Fecha**: {date}

📰 **Tu actividad de hoy**:
• Noticias cargadas: {articles_count}
• Mensajes en conversación: {messages_count}

⏰ **Scheduler**:
• Estado: {"🟢 Activo" if scheduler_status["running"] else "🔴 Inactivo"}
• Hora del noticiario: {scheduler_status["daily_time"]}
• Próxima ejecución: {scheduler_status["next_run"] or "No programada"}

💾 **Base de datos**:
• Total de estados: {db_stats["total_states"]}
• Chats activos: {db_stats["total_chats"]}
    """
    
    await update.message.reply_text(
        status_message,
        parse_mode="Markdown"
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para mensajes de texto (preguntas sobre noticias).
    Ejecuta el grafo en modo question.
    """
    chat_id = update.effective_chat.id
    user_message = update.message.text
    
    if not user_message or len(user_message.strip()) < 3:
        return
    
    logger.info(f"[Telegram] Mensaje de chat_id={chat_id}: '{user_message[:50]}...'")
    
    # Enviar indicador de "escribiendo"
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # Ejecutar el grafo en modo question
        final_state = await run_graph_for_chat(
            chat_id, 
            mode="question", 
            user_input=user_message
        )
        
        # La respuesta ya fue enviada por el nodo publish
        # Si por alguna razón no se envió, enviarla aquí
        if final_state.get("answer") and not final_state.get("audio_path"):
            # El nodo publish debería haber enviado esto
            pass
        
    except Exception as e:
        logger.error(f"[Telegram] Error procesando mensaje: {e}")
        await update.message.reply_text(
            "❌ Ha ocurrido un error procesando tu pregunta. "
            "Por favor, inténtalo de nuevo."
        )


async def daily_news_callback(chat_id: int) -> None:
    """
    Callback para el scheduler del noticiario diario.
    
    Args:
        chat_id: ID del chat para el que generar el noticiario
    """
    logger.info(f"[Scheduler] Generando noticiario para chat_id={chat_id}")
    
    try:
        await run_graph_for_chat(chat_id, mode="daily")
    except Exception as e:
        logger.error(f"[Scheduler] Error generando noticiario para chat_id={chat_id}: {e}")


def main() -> None:
    """
    Función principal que inicia el servicio.
    """
    # Verificar configuración
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN no configurado. Copia .env.example a .env y configúralo.")
        sys.exit(1)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("OPENAI_API_KEY no configurado. El servicio puede no funcionar correctamente.")
    
    logger.info("=" * 60)
    logger.info("🎙️ SERVICIO DE NOTICIAS - INICIANDO")
    logger.info("=" * 60)
    
    # Crear directorio de audio si no existe
    Path("./audio").mkdir(exist_ok=True)
    
    # Inicializar scheduler
    scheduler = get_scheduler()
    scheduler.set_daily_callback(daily_news_callback)
    scheduler.start()
    
    logger.info(f"[Main] Scheduler iniciado. Próximo noticiario: {scheduler.get_next_run_time()}")
    
    # Crear aplicación de Telegram
    application = Application.builder().token(bot_token).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("podcast", podcast_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        message_handler
    ))
    
    logger.info("[Main] Bot de Telegram configurado")
    logger.info("[Main] Iniciando polling...")
    logger.info("=" * 60)
    
    # Iniciar bot en modo polling
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
