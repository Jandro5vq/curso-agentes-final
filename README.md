# 🎙️ News Service - Servicio de Noticias por Telegram

Servicio de generación y consulta de noticiarios por Telegram implementado con **LangGraph** como máquina de estados, **MCPs** para integración de servicios, y **Edge TTS** (Microsoft) para síntesis de voz de alta calidad.

> 🇪🇸 **Enfocado en España**: Noticias de El País, El Mundo, ABC, Marca y más.

## ⚡ Inicio Rápido

```powershell
# 1. Clonar y entrar al directorio
cd news_service

# 2. Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env (ver sección de configuración)

# 5. Ejecutar
python main.py
```

## 🎯 Funcionalidades

1. **Noticiario Diario** (~3 minutos)
   - Generación automática a las 8:00 AM (configurable)
   - Búsqueda de noticias de múltiples fuentes españolas
   - Generación de guion con OpenAI GPT-4o-mini
   - Síntesis de audio con Edge TTS (voz es-ES-AlvaroNeural)
   - Publicación automática en Telegram

2. **Preguntas sobre Noticias**
   - Responde preguntas en texto sobre cualquier tema
   - Busca noticias específicas del tema consultado
   - Respuesta rápida sin audio

3. **Mini-Podcast** (~1 minuto)
   - Podcasts cortos con noticias destacadas
   - Ideal para un vistazo rápido
   - Generación bajo demanda con `/podcast`

## 📁 Estructura del Proyecto

```
news_service/
├── main.py                    # Punto de entrada principal
├── config.py                  # Carga de configuración
├── config.yaml                # Configuración del servicio
├── scheduler.py               # Programador de tareas (APScheduler)
├── requirements.txt           # Dependencias Python
├── .env                       # Variables de entorno (crear desde .env.example)
├── graph/
│   ├── __init__.py
│   └── news_graph.py          # StateGraph de LangGraph
├── nodes/
│   ├── __init__.py
│   ├── reporter.py            # Recopilación de noticias
│   ├── writer.py              # Generación de guiones (OpenAI)
│   └── podcast.py             # Síntesis de voz (Edge TTS)
├── persistence/
│   ├── __init__.py
│   └── state_store.py         # Almacenamiento SQLite
├── mcps/
│   ├── __init__.py
│   ├── news_client.py         # Cliente de noticias (NewsAPI/GNews/RSS)
│   └── telegram_client.py     # Cliente de Telegram
├── data/                      # Base de datos SQLite
├── audio/                     # Archivos de audio generados
└── docs/                      # Documentación
    ├── ARCHITECTURE.md
    ├── QUICKSTART.md
    ├── USER_GUIDE.md
    └── API_REFERENCE.md
```

## 🔄 Flujo LangGraph

```
              ┌─────────────┐
              │    START    │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │  reporter   │  ← Obtiene noticias
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │   router    │  ← Decide flujo según mode
              └──────┬──────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
   [question]    [daily]    [mini_podcast]
       │             │             │
       ▼             └──────┬──────┘
  answer_node                │
       │                     ▼
       │              ┌─────────────┐
       │              │   writer    │  ← Genera guion
       │              └──────┬──────┘
       │                     │
       │                     ▼
       │              ┌─────────────┐
       │              │  tts_node   │  ← Genera audio
       │              └──────┬──────┘
       │                     │
       │                     ▼
       │              ┌─────────────┐
       └────────────► │    send     │  ← Envía a Telegram
                      └──────┬──────┘
                             │
                             ▼
                      ┌─────────────┐
                      │     END     │
                      └─────────────┘
```

## 🛠️ Instalación

Ver [QUICKSTART.md](docs/QUICKSTART.md) para instrucciones detalladas.

```powershell
# Resumen rápido
cd news_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Configurar .env
python main.py
```

## 📱 Comandos de Telegram

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra bienvenida |
| `/news` | Genera podcast completo del día (~3 min) |
| `/podcast` | Genera mini-podcast rápido (~1 min) |
| `/status` | Muestra el estado del servicio |
| `<texto>` | Pregunta sobre cualquier tema de noticias |

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Requeridas
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Recomendadas
NEWSAPI_KEY=...       # https://newsapi.org/

# Opcionales
GNEWS_KEY=...         # https://gnews.io/

# LangSmith (Observabilidad)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=news-service
```

### config.yaml

```yaml
scheduler:
  daily_time: "08:00"
  timezone: "Europe/Madrid"

tts:
  provider: edge_tts
  voice: es-ES-AlvaroNeural

news:
  max_articles: 10
  spanish_sources:
    - el-mundo
    - el-pais
    - marca
    - abc
```

## 📊 Arquitectura

```
┌─────────────┐
│   Telegram  │  ◄── python-telegram-bot (polling)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  LangGraph  │  ◄── StateGraph con 3 flujos
└──────┬──────┘
       │
       ├──► Reporter ──► NewsClient (NewsAPI/GNews/RSS)
       │
       ├──► Writer ──► OpenAI GPT-4o-mini
       │
       └──► TTS ──► Edge TTS (Microsoft)
```

## 📖 Documentación

| Documento | Descripción |
|-----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura técnica completa |
| [QUICKSTART.md](docs/QUICKSTART.md) | Guía de inicio rápido |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Guía de usuario del bot |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Referencia de código |

## 🧪 Testing

```powershell
# Probar que todo está instalado
python -c "import edge_tts; print('TTS OK')"
python -c "from langchain_openai import ChatOpenAI; print('OpenAI OK')"

# Ejecutar el servicio
python main.py
```

## 🔧 Solución de Problemas

### "Conflict: terminated by other getUpdates request"
Solo puede haber una instancia del bot corriendo. Cierra otras terminales.

### "No hay noticias disponibles"
- Verifica NEWSAPI_KEY en .env
- El sistema tiene fallback a Google News RSS

### El bot no responde
- Verifica que el token de Telegram sea correcto
- Asegúrate de ver "Application started" en la terminal

## 📄 Licencia

MIT License
- Asegúrate de tener suficiente espacio en disco
- Verifica que torch esté instalado correctamente
- Prueba con `use_gpu: false` si hay problemas con CUDA

### El audio no se genera
- Verifica que la carpeta `./audio` tenga permisos de escritura
- Comprueba los logs para errores específicos de TTS

## 📄 Licencia

Proyecto académico - Curso de Agentes con IA

## 🤝 Contribuciones

Este proyecto es parte de un curso. Para contribuciones:
1. Respeta la arquitectura establecida
2. No simplifiques ni elimines LangGraph
3. Mantén la estructura de archivos
4. Documenta los cambios
