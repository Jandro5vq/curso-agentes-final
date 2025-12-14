# 🎙️ News Service - Arquitectura del Sistema

## Visión General

News Service es un bot de Telegram que genera podcasts de noticias usando inteligencia artificial. Utiliza **LangGraph** como máquina de estados para orquestar el flujo de trabajo, **LangChain + OpenAI** para generación de contenido, y **Edge TTS** para síntesis de voz.

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM BOT                              │
│  /start  /news  /podcast  /status  [mensajes de texto]          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH STATE MACHINE                     │
│  ┌──────────┐   ┌──────────┐   ┌─────┐   ┌─────────┐            │
│  │ Reporter │ → │  Writer  │ → │ TTS │ → │ Publish │            │
│  └──────────┘   └──────────┘   └─────┘   └─────────┘            │
│                                                                  │
│  ┌────────┐   ┌───────────────────┐   ┌────────────────┐        │
│  │ Router │ → │ Context Evaluator │ → │ Fetch Extra    │        │
│  └────────┘   └───────────────────┘   │ Info / Answer  │        │
│                                       └────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MCP CLIENTS                              │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────┐         │
│  │ NewsClient  │   │  TTSClient   │   │TelegramClient │         │
│  │ (NewsAPI,   │   │ (Edge TTS)   │   │ (send audio/  │         │
│  │  GNews,RSS) │   │              │   │  text)        │         │
│  └─────────────┘   └──────────────┘   └───────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PERSISTENCE                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SQLite: news_state.db                                   │    │
│  │  Key: (chat_id, date) → NewsState (JSON)                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Modos de Operación

### 1. 📰 Modo Daily (Podcast Diario)
**Trigger:** `/news` o scheduler automático a las 08:00

```
Reporter → Writer → TTS → Publish
```

1. **Reporter**: Obtiene 10 noticias de España de múltiples fuentes
2. **Writer**: Genera guion de ~450 palabras (~3 minutos)
3. **TTS**: Sintetiza audio con Edge TTS (voz española)
4. **Publish**: Envía audio al chat de Telegram

### 2. ❓ Modo Question (Preguntas)
**Trigger:** Cualquier mensaje de texto

```
Router → Context Evaluator → [Answer from Memory | Fetch Extra Info → Answer with Augmentation] → Publish
```

1. **Router**: Detecta que es una pregunta
2. **Context Evaluator**: Evalúa si las noticias del día son suficientes
3. **Si contexto suficiente**: Responde directamente
4. **Si contexto insuficiente**: Busca información adicional y responde
5. **Publish**: Envía respuesta de texto

### 3. 🎧 Modo Mini-Podcast
**Trigger:** `/podcast`

```
Reporter → Writer (mini) → TTS → Publish
```

Similar al daily pero con guion más corto (~150 palabras, ~1 minuto).

---

## Estructura de Archivos

```
news_service/
├── main.py                 # Entry point, handlers de Telegram
├── config.yaml             # Configuración del sistema
├── scheduler.py            # APScheduler para podcast diario
├── requirements.txt        # Dependencias Python
├── .env                    # Variables de entorno (API keys)
│
├── graph/                  # LangGraph State Machine
│   ├── __init__.py
│   ├── state.py           # NewsState TypedDict
│   ├── graph.py           # Definición del grafo con nodos y edges
│   └── nodes/             # Nodos del grafo
│       ├── router.py          # Clasifica el modo de operación
│       ├── reporter.py        # Obtiene noticias
│       ├── writer.py          # Genera guiones
│       ├── context_evaluator.py  # Evalúa si hay contexto suficiente
│       ├── fetch_extra_info.py   # Busca información adicional
│       ├── answer.py          # Genera respuestas a preguntas
│       ├── tts.py             # Síntesis de voz
│       └── publish.py         # Publica en Telegram
│
├── mcps/                   # Model Context Protocol Clients
│   ├── __init__.py
│   ├── news_client.py     # Cliente de noticias (NewsAPI, GNews, RSS)
│   ├── tts_client.py      # Cliente TTS (Edge TTS)
│   └── telegram_client.py # Cliente Telegram
│
├── persistence/            # Capa de persistencia
│   ├── __init__.py
│   └── sqlite.py          # StateStore con SQLite
│
├── audio/                  # Archivos de audio generados
├── data/                   # Base de datos SQLite
└── docs/                   # Documentación
```

---

## Estado del Sistema (NewsState)

```python
class NewsState(TypedDict):
    # Identificación
    chat_id: int                    # ID del chat de Telegram
    mode: str                       # "daily" | "question" | "mini_podcast"
    
    # Entrada del usuario
    user_message: str               # Mensaje/pregunta del usuario
    
    # Noticias
    articles: list[dict]            # Lista de artículos obtenidos
    
    # Contenido generado
    script: str                     # Guion del podcast
    audio_path: str                 # Ruta al archivo de audio
    answer: str                     # Respuesta a pregunta
    
    # Flujo de Q&A
    context_sufficient: bool        # ¿Las noticias responden la pregunta?
    extra_info: list[dict]          # Información adicional buscada
    
    # Historial
    conversation: list[dict]        # Historial de conversación
```

---

## Flujo del Grafo LangGraph

```python
# Definición simplificada del grafo
graph = StateGraph(NewsState)

# Nodos
graph.add_node("router", router_node)
graph.add_node("reporter", reporter_node)
graph.add_node("writer", writer_node)
graph.add_node("context_evaluator", context_evaluator_node)
graph.add_node("fetch_extra_info", fetch_extra_info_node)
graph.add_node("answer_from_memory", answer_from_memory_node)
graph.add_node("answer_with_augmentation", answer_with_augmentation_node)
graph.add_node("tts", tts_node)
graph.add_node("publish", publish_node)

# Edges condicionales
graph.add_conditional_edges(
    "router",
    route_by_mode,  # daily/mini_podcast → reporter, question → context_evaluator
)

graph.add_conditional_edges(
    "context_evaluator", 
    route_by_context_evaluation,  # sufficient → answer_from_memory, else → fetch_extra_info
)
```

---

## Fuentes de Noticias

El sistema usa una cadena de fallback para garantizar siempre tener noticias:

```
1. NewsAPI (fuentes españolas)     ← Principal
   └── el-mundo, el-pais, marca, abc-es
   
2. GNews API                       ← Fallback 1
   └── country=es, lang=es
   
3. Google News RSS (España)        ← Fallback 2
   └── hl=es-ES, gl=ES, ceid=ES:es
```

### Filtrado de Noticias
- **Noticias generales**: Últimas 24 horas (con fallback a más antiguas)
- **Búsqueda por tema**: Últimas 72 horas
- **Mínimo garantizado**: 5 artículos siempre

---

## Configuración

### Variables de Entorno (.env)

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...

# News APIs
NEWSAPI_KEY=...
GNEWS_KEY=...           # Opcional

# LangSmith (observabilidad)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=news-service
```

### Archivo de Configuración (config.yaml)

```yaml
openai:
  model: "gpt-4o-mini"
  temperature: 0.7

news:
  country: "es"
  language: "es"
  max_articles: 10

tts:
  backend: "edge"           # edge | coqui
  voice: "es-ES-AlvaroNeural"

scheduler:
  daily_time: "08:00"
  timezone: "Europe/Madrid"

script:
  daily_duration: 180       # 3 minutos
  mini_duration: 60         # 1 minuto
```

---

## Comandos de Telegram

| Comando | Descripción |
|---------|-------------|
| `/start` | Mensaje de bienvenida e instrucciones |
| `/news` | Genera podcast con noticias del día (~3 min) |
| `/podcast` | Genera mini-podcast (~1 min) |
| `/status` | Muestra estado del servicio |
| `[texto]` | Pregunta sobre las noticias |

---

## Ejecución

```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac

# Ejecutar el servicio
python main.py
```

### Logs esperados al iniciar:

```
🎙️ SERVICIO DE NOTICIAS - INICIANDO
[Scheduler] Configurado para 08:00 (Europe/Madrid)
[Main] Bot de Telegram configurado
[Main] Iniciando polling...
Application started
```

---

## Diagrama de Secuencia: /news

```
Usuario          Telegram         main.py          Graph           NewsClient       OpenAI          EdgeTTS
   │                │                │               │                 │               │               │
   │──/news────────▶│                │               │                 │               │               │
   │                │──handler──────▶│               │                 │               │               │
   │                │                │──invoke──────▶│                 │               │               │
   │                │                │               │──fetch_news────▶│               │               │
   │                │                │               │◀────articles────│               │               │
   │                │                │               │──generate_script─────────────▶│               │
   │                │                │               │◀────────script────────────────│               │
   │                │                │               │──synthesize───────────────────────────────────▶│
   │                │                │               │◀────────audio_path────────────────────────────│
   │                │                │◀──result──────│                 │               │               │
   │                │◀─send_audio────│               │                 │               │               │
   │◀───audio──────│                │               │                 │               │               │
```

---

## Dependencias Principales

| Paquete | Versión | Uso |
|---------|---------|-----|
| langgraph | ≥0.2.0 | Máquina de estados |
| langchain-openai | ≥0.2.0 | Integración OpenAI |
| python-telegram-bot | ≥21.0 | Bot de Telegram |
| edge-tts | ≥6.1.0 | Síntesis de voz |
| apscheduler | ≥3.10.0 | Programación de tareas |
| requests | ≥2.31.0 | HTTP para APIs de noticias |
| beautifulsoup4 | ≥4.12.0 | Parsing RSS |

---

## Observabilidad con LangSmith

Cuando está configurado, LangSmith captura:

- ✅ Cada ejecución del grafo
- ✅ Inputs/outputs de cada nodo
- ✅ Llamadas a OpenAI (prompts, respuestas, tokens)
- ✅ Latencias y errores

Dashboard: https://smith.langchain.com/

---

## Troubleshooting

### Error: "Conflict: terminated by other getUpdates request"
**Causa**: Múltiples instancias del bot corriendo.
**Solución**: Cerrar todas las terminales y ejecutar solo una instancia.

### Error: "No se encontraron noticias"
**Causa**: Filtro de fecha muy estricto o APIs sin respuesta.
**Solución**: El sistema ahora tiene fallback automático a noticias más antiguas.

### Error: "OPENAI_API_KEY no configurado"
**Solución**: Verificar archivo `.env` con las claves correctas.

---

## Próximas Mejoras

- [ ] Soporte para múltiples idiomas
- [ ] Categorías de noticias personalizables
- [ ] Resumen semanal automático
- [ ] Voces alternativas configurables
- [ ] Integración con más fuentes de noticias
