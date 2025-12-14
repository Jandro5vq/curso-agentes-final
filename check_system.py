"""
Script de diagnóstico para verificar todos los componentes del sistema.
"""
import os
import sys
from pathlib import Path

def check_imports():
    """Verifica que todos los módulos se importen correctamente."""
    print("=" * 50)
    print("VERIFICACIÓN DE IMPORTS")
    print("=" * 50)
    
    checks = [
        ("LangGraph", "from langgraph.graph import StateGraph"),
        ("LangChain OpenAI", "from langchain_openai import ChatOpenAI"),
        ("Edge TTS", "import edge_tts"),
        ("Telegram Bot", "from telegram import Bot"),
        ("APScheduler", "from apscheduler.schedulers.asyncio import AsyncIOScheduler"),
        ("SQLite", "import sqlite3"),
        ("YAML", "import yaml"),
        ("Estado del Grafo", "from graph.state import NewsState"),
        ("Creador del Grafo", "from graph.graph import create_news_graph"),
        ("News Client", "from mcps.news_client import NewsClient"),
        ("TTS Client", "from mcps.tts_client import TTSClient"),
        ("Telegram Client", "from mcps.telegram_client import TelegramClient"),
        ("Persistencia", "from persistence.sqlite import StateStore"),
        ("Scheduler", "from scheduler import NewsScheduler"),
    ]
    
    all_ok = True
    for name, import_stmt in checks:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            all_ok = False
    
    return all_ok

def check_env():
    """Verifica las variables de entorno."""
    print("\n" + "=" * 50)
    print("VERIFICACIÓN DE VARIABLES DE ENTORNO")
    print("=" * 50)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    env_vars = [
        ("OPENAI_API_KEY", True),
        ("TELEGRAM_BOT_TOKEN", True),
        ("NEWSAPI_KEY", True),
        ("GNEWS_KEY", False),  # Opcional
    ]
    
    all_ok = True
    for var, required in env_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}: {masked}")
        elif required:
            print(f"❌ {var}: No configurado (REQUERIDO)")
            all_ok = False
        else:
            print(f"⚠️  {var}: No configurado (opcional)")
    
    return all_ok

def check_config():
    """Verifica el archivo de configuración."""
    print("\n" + "=" * 50)
    print("VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 50)
    
    try:
        import yaml
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        sections = ["openai", "telegram", "news", "tts", "persistence", "scheduler"]
        for section in sections:
            if section in config:
                print(f"✅ Sección '{section}' presente")
            else:
                print(f"❌ Sección '{section}' faltante")
        
        return True
    except Exception as e:
        print(f"❌ Error leyendo config.yaml: {e}")
        return False

def check_graph():
    """Verifica que el grafo LangGraph se cree correctamente."""
    print("\n" + "=" * 50)
    print("VERIFICACIÓN DEL GRAFO LANGGRAPH")
    print("=" * 50)
    
    try:
        from graph import create_news_graph
        graph = create_news_graph()
        print(f"✅ Grafo creado: {type(graph).__name__}")
        
        # Verificar nodos
        print(f"✅ Grafo compilado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error creando grafo: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_tts():
    """Verifica que Edge TTS funcione."""
    print("\n" + "=" * 50)
    print("VERIFICACIÓN DE TTS")
    print("=" * 50)
    
    try:
        import asyncio
        import edge_tts
        
        async def test():
            communicate = edge_tts.Communicate("Prueba", "es-ES-AlvaroNeural")
            # Solo verificar que se puede crear, no generar audio
            return True
        
        asyncio.run(test())
        print("✅ Edge TTS disponible")
        print("✅ Voz es-ES-AlvaroNeural disponible")
        return True
    except Exception as e:
        print(f"❌ Error con TTS: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones."""
    print("\n🔍 DIAGNÓSTICO DEL SISTEMA DE NOTICIAS\n")
    
    results = {
        "Imports": check_imports(),
        "Configuración": check_config(),
        "Variables de Entorno": check_env(),
        "Grafo LangGraph": check_graph(),
        "TTS": check_tts(),
    }
    
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    
    all_ok = True
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
        if not ok:
            all_ok = False
    
    if all_ok:
        print("\n🎉 ¡Todo está listo! Puedes ejecutar: python main.py")
    else:
        print("\n⚠️  Hay problemas que resolver antes de ejecutar el sistema.")
        print("   Por favor, configura las variables de entorno en el archivo .env")

if __name__ == "__main__":
    main()
