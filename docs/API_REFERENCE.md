# 📚 Referencia de API

Este documento describe las clases y funciones principales del servicio de noticias.

---

## 📁 Estructura de Módulos

```
news_service/
├── main.py              # Punto de entrada
├── config.py            # Carga de configuración
├── scheduler.py         # Programador de tareas
├── graph/
│   └── news_graph.py    # StateGraph de LangGraph
├── mcps/
│   ├── news_client.py   # Cliente de noticias
│   └── telegram_client.py # Cliente de Telegram
├── nodes/
│   ├── reporter.py      # Nodo recopilador
│   ├── writer.py        # Nodo escritor
│   └── podcast.py       # Nodo TTS
└── persistence/
    └── state_store.py   # Almacenamiento SQLite
```

---

## 🔄 NewsState (TypedDict)

Estructura del estado que fluye por el grafo de LangGraph.

```python
class NewsState(TypedDict):
    mode: Literal["daily", "question", "mini_podcast"]
    chat_id: int
    user_question: Optional[str]
    articles: List[Dict[str, Any]]
    script: str
    audio_path: str
    response_text: str
    metadata: Dict[str, Any]
```

### Campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `mode` | str | Modo de ejecución: "daily", "question", "mini_podcast" |
| `chat_id` | int | ID del chat de Telegram |
| `user_question` | str | Pregunta del usuario (solo en mode="question") |
| `articles` | list | Lista de artículos de noticias |
| `script` | str | Guion generado por el LLM |
| `audio_path` | str | Ruta al archivo de audio generado |
| `response_text` | str | Texto de respuesta (para preguntas) |
| `metadata` | dict | Metadatos adicionales |

---

## 📰 NewsClient

Cliente para obtener noticias de múltiples fuentes.

### Ubicación
`mcps/news_client.py`

### Inicialización
```python
from mcps.news_client import NewsClient

client = NewsClient()
```

### Métodos

#### `fetch_general_news(max_articles: int = 10) -> List[Dict]`

Obtiene noticias generales priorizando fuentes españolas.

```python
articles = client.fetch_general_news(max_articles=10)

# Retorna:
[
    {
        "title": "Título de la noticia",
        "description": "Descripción o resumen",
        "source": "El País",
        "published_at": "2024-01-15T10:30:00Z",
        "url": "https://..."
    },
    ...
]
```

#### `fetch_topic_news(topic: str, max_articles: int = 5) -> List[Dict]`

Busca noticias sobre un tema específico.

```python
articles = client.fetch_topic_news("inteligencia artificial", max_articles=5)
```

### Fuentes de datos (en orden de prioridad):

1. **NewsAPI** - Fuentes españolas configuradas
2. **GNews** - Agregador alternativo
3. **Google News RSS** - RSS de Google News España

### Filtrado de fechas

El cliente filtra automáticamente noticias antiguas pero garantiza un mínimo de artículos:

```python
def _filter_today_articles(
    articles: List[Dict], 
    max_hours: int = 48, 
    min_articles: int = 5
) -> List[Dict]
```

---

## 📱 TelegramClient

Cliente para enviar mensajes y audio a Telegram.

### Ubicación
`mcps/telegram_client.py`

### Inicialización
```python
from mcps.telegram_client import TelegramClient

client = TelegramClient()
```

### Métodos

#### `async send_audio(chat_id: int, audio_path: str, caption: str = "") -> bool`

Envía un archivo de audio a un chat.

```python
await client.send_audio(
    chat_id=123456789,
    audio_path="./audio/podcast_20240115.mp3",
    caption="🎙️ Podcast del día"
)
```

#### `async send_message(chat_id: int, text: str) -> bool`

Envía un mensaje de texto.

```python
await client.send_message(
    chat_id=123456789,
    text="¡Hola! Aquí tienes las noticias..."
)
```

---

## 🔊 PodcastNode

Nodo que genera audio usando Edge TTS.

### Ubicación
`nodes/podcast.py`

### Función principal
```python
async def generate_audio(state: NewsState) -> NewsState:
    """
    Genera audio a partir del script en el estado.
    
    Args:
        state: Estado con el campo 'script' poblado
        
    Returns:
        Estado con 'audio_path' actualizado
    """
```

### Configuración de voz

Configurado en `config.yaml`:
```yaml
tts:
  provider: edge_tts
  voice: es-ES-AlvaroNeural
  output_dir: ./audio
```

### Voces disponibles (español):
- `es-ES-AlvaroNeural` - Masculina, España
- `es-ES-ElviraNeural` - Femenina, España
- `es-MX-DaliaNeural` - Femenina, México
- `es-MX-JorgeNeural` - Masculina, México

---

## ✍️ WriterNode

Nodo que genera el guion del podcast usando LLM.

### Ubicación
`nodes/writer.py`

### Función principal
```python
async def write_script(state: NewsState) -> NewsState:
    """
    Genera un guion de podcast basado en los artículos.
    
    Args:
        state: Estado con 'articles' y 'mode' poblados
        
    Returns:
        Estado con 'script' generado
    """
```

### Comportamiento por modo:

| Modo | Longitud | Estilo |
|------|----------|--------|
| `daily` | ~500 palabras | Formal, informativo |
| `mini_podcast` | ~200 palabras | Conciso, destacados |
| `question` | Variable | Respuesta directa |

---

## 📊 ReporterNode

Nodo que recopila noticias según el modo.

### Ubicación
`nodes/reporter.py`

### Función principal
```python
async def fetch_news(state: NewsState) -> NewsState:
    """
    Obtiene noticias según el modo.
    
    - daily: Noticias generales (10 artículos)
    - mini_podcast: Noticias generales (5 artículos)
    - question: Noticias por tema (5 artículos)
    """
```

---

## 🗃️ StateStore

Almacenamiento de estado en SQLite.

### Ubicación
`persistence/state_store.py`

### Inicialización
```python
from persistence.state_store import StateStore

store = StateStore(db_path="./data/news_state.db")
```

### Métodos

#### `save_state(chat_id: int, date: str, state: NewsState) -> None`
```python
store.save_state(
    chat_id=123456789,
    date="2024-01-15",
    state=current_state
)
```

#### `get_state(chat_id: int, date: str) -> Optional[NewsState]`
```python
saved = store.get_state(123456789, "2024-01-15")
if saved:
    print(f"Artículos guardados: {len(saved['articles'])}")
```

#### `has_received_today(chat_id: int) -> bool`
```python
if not store.has_received_today(chat_id):
    # Enviar podcast
    pass
```

---

## 📅 Scheduler

Programador de tareas usando APScheduler.

### Ubicación
`scheduler.py`

### Configuración
```python
from scheduler import setup_scheduler

scheduler = setup_scheduler(
    send_podcast_callback=send_daily_podcast,
    time="08:00",
    timezone="Europe/Madrid"
)
```

### Funciones

#### `setup_scheduler(callback, time, timezone) -> BackgroundScheduler`

Configura el programador para ejecutar el callback diariamente.

```python
def my_callback(chat_id):
    # Ejecutar grafo de LangGraph
    asyncio.run(process_daily(chat_id))

scheduler = setup_scheduler(
    send_podcast_callback=my_callback,
    time="08:00",
    timezone="Europe/Madrid"
)
```

---

## 🔀 NewsGraph

Grafo de estados de LangGraph.

### Ubicación
`graph/news_graph.py`

### Inicialización
```python
from graph.news_graph import create_news_graph

graph = create_news_graph()
```

### Ejecución
```python
# Ejecutar el grafo
initial_state = {
    "mode": "daily",
    "chat_id": 123456789,
    "user_question": None,
    "articles": [],
    "script": "",
    "audio_path": "",
    "response_text": "",
    "metadata": {}
}

result = await graph.ainvoke(initial_state)
```

### Nodos del grafo:

```
┌─────────────┐
│    START    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  reporter   │  ← Recolecta noticias
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   router    │  ← Decide siguiente paso
└──────┬──────┘
       │
       ├── mode="question" ──► answer_question ──► END
       │
       └── mode="daily"|"mini_podcast"
                │
                ▼
          ┌─────────────┐
          │   writer    │  ← Genera guion
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │  tts_node   │  ← Genera audio
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │    send     │  ← Envía a Telegram
          └──────┬──────┘
                 │
                 ▼
            ┌────────┐
            │  END   │
            └────────┘
```

---

## ⚙️ Config

Carga de configuración desde YAML y variables de entorno.

### Ubicación
`config.py`

### Uso
```python
from config import config

# Acceder a configuración
voice = config["tts"]["voice"]
api_key = config["openai"]["api_key"]
daily_time = config["scheduler"]["daily_time"]
```

### Estructura de config.yaml:
```yaml
openai:
  model: gpt-4o-mini
  temperature: 0.7

telegram:
  bot_token: ${TELEGRAM_BOT_TOKEN}

tts:
  provider: edge_tts
  voice: es-ES-AlvaroNeural
  output_dir: ./audio

news:
  newsapi_key: ${NEWSAPI_KEY}
  gnews_key: ${GNEWS_KEY}
  max_articles: 10
  spanish_sources:
    - el-mundo
    - el-pais
    - marca
    - abc

scheduler:
  daily_time: "08:00"
  timezone: Europe/Madrid

langsmith:
  enabled: true
  project: news-service
```

---

## 🔧 Variables de Entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `OPENAI_API_KEY` | ✅ | API key de OpenAI |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token del bot de Telegram |
| `NEWSAPI_KEY` | ⚠️ | API key de NewsAPI |
| `GNEWS_KEY` | ❌ | API key de GNews |
| `LANGCHAIN_TRACING_V2` | ❌ | Activar trazas de LangSmith |
| `LANGCHAIN_API_KEY` | ❌ | API key de LangSmith |
| `LANGCHAIN_PROJECT` | ❌ | Nombre del proyecto en LangSmith |

---

## 🧪 Ejemplos de Uso

### Ejecutar podcast manual
```python
import asyncio
from graph.news_graph import create_news_graph

async def main():
    graph = create_news_graph()
    
    result = await graph.ainvoke({
        "mode": "daily",
        "chat_id": 123456789,
        "articles": [],
        "script": "",
        "audio_path": "",
        "response_text": "",
        "metadata": {}
    })
    
    print(f"Audio generado: {result['audio_path']}")

asyncio.run(main())
```

### Obtener noticias sin generar audio
```python
from mcps.news_client import NewsClient

client = NewsClient()
articles = client.fetch_general_news(max_articles=10)

for article in articles:
    print(f"- {article['title']}")
    print(f"  Fuente: {article['source']}")
    print(f"  Fecha: {article['published_at']}")
    print()
```

### Generar solo audio
```python
import asyncio
import edge_tts

async def generate_audio(text, output_path):
    communicate = edge_tts.Communicate(text, "es-ES-AlvaroNeural")
    await communicate.save(output_path)

asyncio.run(generate_audio(
    "Buenos días, estas son las noticias del día.",
    "./test_audio.mp3"
))
```
