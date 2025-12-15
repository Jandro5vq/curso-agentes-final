# 🎙️ La IA Dice - Documentación Técnica del Proyecto

## Presentación del Sistema Multi-Agente de Noticias

---

## 📋 Índice

1. [Visión General](#-visión-general)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Sistema Multi-Agente](#-sistema-multi-agente)
4. [Grafo LangGraph](#-grafo-langgraph)
5. [Guardrails y Validadores](#-guardrails-y-validadores)
6. [Herramientas MCP](#-herramientas-mcp)
7. [Flujos de Ejecución](#-flujos-de-ejecución)
8. [Stack Tecnológico](#-stack-tecnológico)
9. [Diagramas](#-diagramas)

---

## 🎯 Visión General

**"La IA Dice"** es un servicio de podcast de noticias automatizado que utiliza una **arquitectura multi-agente** para:

- 📰 **Recopilar** noticias de múltiples fuentes en tiempo real
- ✍️ **Transformar** noticias en guiones profesionales de podcast
- 🎧 **Producir** audio de alta calidad mediante síntesis de voz
- 📱 **Distribuir** contenido automáticamente vía Telegram

### Características Principales

| Característica | Descripción |
|---------------|-------------|
| **Multi-Agente** | 4 agentes especializados que colaboran |
| **LangGraph** | Orquestación mediante grafos de estado |
| **Tool Calling** | Agentes con herramientas MCP reales |
| **Guardrails** | Validación de entrada y contenido |
| **TTS** | Síntesis de voz con Edge TTS |
| **Tiempo Real** | Noticias actualizadas al momento |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LA IA DICE                                               │
│                   Sistema Multi-Agente de Noticias                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐     ┌─────────────────────────────────────────┐    │
│  │   Telegram  │────▶│           LANGGRAPH ENGINE               │    │
│  │    Bot      │     │  ┌─────────────────────────────────────┐ │    │
│  └─────────────┘     │  │         MULTIAGENT GRAPH            │ │    │
│                      │  │  ┌───────┐  ┌────────┐  ┌─────────┐ │ │    │
│                      │  │  │Router │─▶│Reporter│─▶│ Writer  │ │ │    │
│                      │  │  └───────┘  └────────┘  └─────────┘ │ │    │
│  ┌─────────────┐     │  │      │                       │      │ │    │
│  │  Dashboard  │     │  │      │    ┌──────────┐       │      │ │    │
│  │    Web      │     │  │      └───▶│ Answer   │       ▼      │ │    │
│  └─────────────┘     │  │           └──────────┘  ┌─────────┐ │ │    │
│                      │  │                         │Producer │ │ │    │
│                      │  │                         └─────────┘ │ │    │
│                      │  └─────────────────────────────────────┘ │    │
│                      └─────────────────────────────────────────┘    │
│                                     │                                │
│          ┌──────────────────────────┼──────────────────────────┐    │
│          ▼                          ▼                          ▼    │
│  ┌─────────────┐           ┌─────────────┐            ┌───────────┐ │
│  │   MCP Tools │           │ Guardrails  │            │    LLM    │ │
│  │ ┌─────────┐ │           │ ┌─────────┐ │            │ (GPT-4o-  │ │
│  │ │NewsAPI  │ │           │ │Input    │ │            │   mini)   │ │
│  │ │Tavily   │ │           │ │Guardrail│ │            └───────────┘ │
│  │ │EdgeTTS  │ │           │ │Script   │ │                          │
│  │ │Telegram │ │           │ │Guardrail│ │                          │
│  │ └─────────┘ │           │ │Content  │ │                          │
│  └─────────────┘           │ │Validator│ │                          │
│                            │ └─────────┘ │                          │
│                            └─────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Capas del Sistema

| Capa | Componentes | Responsabilidad |
|------|-------------|-----------------|
| **Interfaz** | Telegram Bot, Dashboard Web | Entrada/salida de usuarios |
| **Orquestación** | LangGraph, MultiAgentGraph | Gestión del flujo de trabajo |
| **Agentes** | Orchestrator, Reporter, Writer, Producer | Procesamiento inteligente |
| **Validación** | Guardrails, Validators | Seguridad y calidad |
| **Herramientas** | MCP Tools, APIs externas | Capacidades de acción |

---

## 🤖 Sistema Multi-Agente

### Arquitectura de Agentes

El sistema implementa **4 agentes especializados** que colaboran mediante un patrón de delegación:

```
                    ┌──────────────────────┐
                    │   ORCHESTRATOR       │
                    │   (Agente Maestro)   │
                    │                      │
                    │ • Coordina flujos    │
                    │ • Toma decisiones    │
                    │ • Maneja errores     │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    REPORTER     │  │     WRITER      │  │    PRODUCER     │
│                 │  │                 │  │                 │
│ 📰 Obtiene      │  │ ✍️ Genera       │  │ 🎧 Produce      │
│    noticias     │  │    guiones      │  │    audio        │
│                 │  │                 │  │                 │
│ Tools:          │  │ Capacidad:      │  │ Tools:          │
│ • fetch_news    │  │ • LLM directo   │  │ • synthesize    │
│ • fetch_topic   │  │ • Creatividad   │  │ • send_audio    │
│ • search_web    │  │                 │  │ • send_message  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Descripción de Agentes

#### 1. 🎯 OrchestratorAgent (Maestro)
```python
class OrchestratorAgent:
    """Coordina todo el sistema multi-agente."""
    
    Responsabilidades:
    - Recibir solicitudes del usuario
    - Decidir qué agentes invocar
    - Coordinar el flujo entre agentes
    - Manejar errores y reintentos
    
    LLM: GPT-4o-mini (temperature=0.3)
```

#### 2. 📰 ReporterAgent (Especialista en Noticias)
```python
class ReporterAgent:
    """Obtiene noticias usando herramientas MCP."""
    
    Tools disponibles:
    - fetch_general_news_tool: Noticias generales del día
    - fetch_topic_news_tool: Noticias por tema específico
    - search_web_news_tool: Búsqueda web con Tavily
    
    Implementación: create_react_agent (LangGraph prebuilt)
```

#### 3. ✍️ WriterAgent (Especialista en Guiones)
```python
class WriterAgent:
    """Transforma noticias en guiones de podcast."""
    
    Características:
    - LLM directo sin tools externos
    - Alta creatividad (temperature=0.7)
    - Validación con ScriptGuardrail
    
    Formatos soportados:
    - Daily: ~500-600 palabras (~3 min)
    - Píldora: ~200-250 palabras (~1 min)
```

#### 4. 🎧 ProducerAgent (Especialista en Producción)
```python
class ProducerAgent:
    """Produce audio y distribuye contenido."""
    
    Tools disponibles:
    - synthesize_speech_tool: TTS con Edge TTS
    - send_telegram_audio_tool: Envío de audio
    - send_telegram_message_tool: Envío de texto
    
    Implementación: create_react_agent (LangGraph prebuilt)
```

---

## 📊 Grafo LangGraph

### Estructura del Grafo

El sistema utiliza **LangGraph** para orquestar el flujo de trabajo mediante un **grafo de estados**:

```
                         ┌─────────┐
                         │  START  │
                         └────┬────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │     ROUTER      │◄─── InputGuardrail
                    │  (Entry Point)  │     (Validación)
                    └────────┬────────┘
                              │
                              ▼
    ┌────────────────────────────────────────────────────┐
    │                    REPORTER                        │
    │              🤖 Sub-Agent with Tools               │
    │    ┌─────────────────────────────────────────┐     │
    │    │ Tools:                                  │     │
    │    │  • fetch_general_news_tool              │     │
    │    │  • fetch_topic_news_tool                │     │
    │    │  • search_web_news_tool                 │     │
    │    └─────────────────────────────────────────┘     │
    └────────────────────────┬───────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      [daily/mini_podcast]              [question]
              │                               │
              ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │     WRITER      │             │     ANSWER      │
    │  🤖 Sub-Agent   │             │   🤖 LLM +      │
    │  + Guardrail    │◄───────────▶│   Telegram Tool │
    └────────┬────────┘             └────────┬────────┘
              │                               │
              ▼                               │
    ┌────────────────────────────────┐       │
    │           PRODUCER             │       │
    │      🤖 Sub-Agent with Tools   │       │
    │  ┌──────────────────────────┐  │       │
    │  │ Tools:                   │  │       │
    │  │  • synthesize_speech     │  │       │
    │  │  • send_telegram_audio   │  │       │
    │  │  • send_telegram_message │  │       │
    │  └──────────────────────────┘  │       │
    └────────────────┬───────────────┘       │
                      │                       │
                      └───────────┬───────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    FINALIZE     │
                         └────────┬────────┘
                                  │
                                  ▼
                            ┌─────────┐
                            │   END   │
                            └─────────┘
```

### Estado del Grafo (MultiAgentState)

```python
class MultiAgentState(TypedDict):
    """Estado compartido del sistema multi-agente."""
    
    # Identificación
    chat_id: int                    # ID del chat de Telegram
    date: str                       # Fecha (YYYY-MM-DD)
    
    # Modo de operación
    mode: Literal["daily", "mini_podcast", "question"]
    user_input: str | None          # Pregunta o tema del usuario
    
    # Datos intermedios
    news_content: str | None        # Noticias obtenidas por Reporter
    script: str | None              # Guion generado por Writer
    audio_path: str | None          # Ruta del audio generado
    answer: str | None              # Respuesta textual
    
    # Seguimiento de ejecución
    current_agent: str | None       # Agente actualmente en ejecución
    agent_history: list[AgentStep]  # Historial de pasos
    
    # Estado final
    success: bool
    error: str | None
    
    # Metadatos
    metadata: dict[str, Any]
```

### Routing Condicional

```python
def route_after_reporter(state: MultiAgentState) -> Literal["writer", "answer"]:
    """Después del reporter, decidimos si generar guion o responder."""
    mode = state["mode"]
    
    if mode == "question":
        return "answer"    # Respuesta textual directa
    else:
        return "writer"    # Generar guion para audio
```

---

## 🛡️ Guardrails y Validadores

El sistema implementa **3 capas de validación** para garantizar seguridad y calidad:

### 1. InputGuardrail - Validación de Entrada

```python
class InputGuardrail:
    """Valida entradas del usuario antes del procesamiento."""
    
    Protecciones:
    ├── Prompt Injection Detection
    │   └── Patrones: "ignore previous", "system:", "[INST]", etc.
    ├── Prohibited Topics
    │   └── Contenido violento, ilegal, adulto
    ├── Suspicious Characters
    │   └── Caracteres de control, zero-width
    └── Length Validation
        └── Min: 2 chars, Max: 500 chars
```

**Ubicación en el flujo:** Nodo `router_node` (primera validación)

### 2. ScriptGuardrail - Validación de Guiones

```python
class ScriptGuardrail:
    """Valida guiones antes de la producción de audio."""
    
    Validaciones:
    ├── Longitud por Tipo
    │   ├── Daily: 400-700 palabras (~3 min)
    │   └── Píldora: 150-300 palabras (~1 min)
    ├── Estructura de Podcast
    │   ├── Apertura obligatoria ("La IA Dice", "Hola", etc.)
    │   └── Cierre obligatorio ("Hasta pronto", etc.)
    ├── Formato
    │   └── Sin markdown, sin placeholders
    └── Contenido
        └── Sin alucinaciones, sin contenido sensible
```

**Ubicación en el flujo:** `WriterAgent.invoke()` (después de generación)

### 3. ContentValidator - Validación General

```python
class ContentValidator:
    """Validador base para cualquier tipo de contenido."""
    
    Capacidades:
    ├── validate_length()        # Longitud apropiada
    ├── validate_sensitive()     # Contenido sensible
    ├── validate_hallucinations()# Detección de alucinaciones
    ├── validate_script_format() # Formato de guion
    └── sanitize_for_tts()       # Limpieza para síntesis
```

### Diagrama de Validación

```
Usuario Input ──▶ InputGuardrail ──▶ Router
                      │
                      ▼ (si falla)
                 ❌ Error Response

Reporter Output ──▶ [Sin guardrail directo]

Writer Output ──▶ ScriptGuardrail ──▶ Producer
                      │
                      ▼ (si falla)
                 ❌ Regeneración o Error

Producer Output ──▶ ContentValidator.sanitize_for_tts() ──▶ TTS
```

---

## 🔧 Herramientas MCP

### Model Context Protocol (MCP)

El sistema utiliza herramientas compatibles con MCP para dar capacidades reales a los agentes:

### News Tools (Reporter)

| Tool | Descripción | API Backend |
|------|-------------|-------------|
| `fetch_general_news_tool` | Noticias generales del día | NewsAPI |
| `fetch_topic_news_tool` | Noticias por tema específico | NewsAPI |
| `search_web_news_tool` | Búsqueda web avanzada | Tavily Search |

```python
@tool
def fetch_general_news_tool(max_articles: int = 10, country: str = "es") -> str:
    """Obtiene las noticias generales más importantes de actualidad."""
    client = NewsClient()
    articles = client.fetch_general_news(max_articles=max_articles)
    return format_articles(articles)
```

### TTS Tools (Producer)

| Tool | Descripción | Backend |
|------|-------------|---------|
| `synthesize_speech_tool` | Convierte texto a audio | Edge TTS |

```python
@tool
def synthesize_speech_tool(text: str, voice: str = "es-ES-AlvaroNeural") -> str:
    """Genera audio a partir de texto usando Edge TTS."""
    client = TTSClient()
    audio_path = client.synthesize(text, voice=voice)
    return audio_path
```

### Telegram Tools (Producer)

| Tool | Descripción |
|------|-------------|
| `send_telegram_message_tool` | Envía mensajes de texto |
| `send_telegram_audio_tool` | Envía archivos de audio |

```python
@tool
def send_telegram_audio_tool(chat_id: int, audio_path: str, caption: str) -> str:
    """Envía un archivo de audio por Telegram."""
    client = TelegramClient()
    success = client.send_audio(chat_id, audio_path, caption)
    return "Audio enviado" if success else "Error al enviar"
```

---

## 🔄 Flujos de Ejecución

### Flujo 1: Daily Podcast (~3 minutos)

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLUJO DAILY PODCAST                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ENTRADA                                                      │
│     └── /daily o comando programado                              │
│                                                                  │
│  2. ROUTER                                                       │
│     └── mode = "daily"                                           │
│     └── InputGuardrail ✓                                         │
│                                                                  │
│  3. REPORTER                                                     │
│     └── Tool: fetch_general_news_tool(max=10)                    │
│     └── Output: 10 noticias variadas de España                   │
│                                                                  │
│  4. WRITER                                                       │
│     └── Input: Noticias del reporter                             │
│     └── Generación: Guion completo ~550 palabras                 │
│     └── ScriptGuardrail ✓                                        │
│     └── Output: Guion estructurado con apertura/cierre           │
│                                                                  │
│  5. PRODUCER                                                     │
│     └── Tool 1: synthesize_speech_tool(guion)                    │
│     └── Tool 2: send_telegram_audio_tool(audio, chat_id)         │
│     └── Output: Audio enviado a Telegram                         │
│                                                                  │
│  6. FINALIZE                                                     │
│     └── success = True                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo 2: Píldora Temática (~1 minuto)

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLUJO PÍLDORA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ENTRADA                                                      │
│     └── /podcast inteligencia artificial                         │
│     └── user_input = "inteligencia artificial"                   │
│                                                                  │
│  2. ROUTER                                                       │
│     └── mode = "mini_podcast"                                    │
│     └── InputGuardrail ✓ (valida el tema)                        │
│                                                                  │
│  3. REPORTER                                                     │
│     └── Tool: fetch_topic_news_tool(topic="IA", max=5)           │
│     └── Output: 5 noticias sobre IA                              │
│                                                                  │
│  4. WRITER                                                       │
│     └── script_type = "pildora"                                  │
│     └── topic = "inteligencia artificial"                        │
│     └── Generación: Guion corto ~220 palabras                    │
│     └── ScriptGuardrail ✓                                        │
│                                                                  │
│  5. PRODUCER                                                     │
│     └── Caption: "💊 La IA Dice - Píldora: IA"                   │
│     └── Tools: synthesize + send_audio                           │
│                                                                  │
│  6. FINALIZE                                                     │
│     └── success = True                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo 3: Pregunta (Respuesta Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLUJO QUESTION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ENTRADA                                                      │
│     └── "¿Qué está pasando con el precio del petróleo?"          │
│                                                                  │
│  2. ROUTER                                                       │
│     └── mode = "question"                                        │
│     └── InputGuardrail ✓                                         │
│                                                                  │
│  3. REPORTER                                                     │
│     └── Tool: search_web_news_tool("precio petróleo")            │
│     └── Output: Noticias relevantes                              │
│                                                                  │
│  4. ANSWER (no Writer)                                           │
│     └── LLM genera respuesta basada en noticias                  │
│     └── Tool: send_telegram_message_tool                         │
│     └── Output: Respuesta textual enviada                        │
│                                                                  │
│  5. FINALIZE                                                     │
│     └── answer = respuesta generada                              │
│     └── success = True                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Lenguaje y Framework

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Lenguaje | Python | 3.11+ |
| Framework de Agentes | LangGraph | Latest |
| LLM Framework | LangChain | Latest |
| Web Framework | Flask | 3.x |

### APIs y Servicios

| Servicio | Uso | Tipo |
|----------|-----|------|
| OpenAI GPT-4o-mini | LLM principal | API |
| NewsAPI | Fuente de noticias | API |
| Tavily Search | Búsqueda web | API |
| Edge TTS | Síntesis de voz | Local |
| Telegram Bot API | Distribución | API |

### Dependencias Principales

```txt
# Core
langgraph>=0.2.0
langchain>=0.3.0
langchain-openai>=0.2.0

# APIs
tavily-python>=0.5.0
edge-tts>=6.1.0
python-telegram-bot>=21.0

# Web
flask>=3.0.0

# Utils
pyyaml>=6.0
python-dotenv>=1.0.0
```

### Estructura de Archivos

```
news_service/
├── main_multiagent.py      # Punto de entrada principal
├── config.yaml             # Configuración del sistema
├── requirements.txt        # Dependencias
│
├── agents/                 # Agentes del sistema
│   ├── orchestrator.py     # Agente maestro
│   ├── reporter.py         # Agente de noticias
│   ├── writer.py           # Agente de guiones
│   └── producer.py         # Agente de producción
│
├── graph/                  # Grafo LangGraph
│   ├── multiagent_graph.py # Definición del grafo
│   └── multiagent_state.py # Estado tipado
│
├── guardrails/             # Validadores
│   ├── content_validator.py
│   ├── script_guardrail.py
│   └── input_guardrail.py
│
├── tools/                  # Herramientas MCP
│   ├── news_tools.py
│   ├── tts_tools.py
│   └── telegram_tools.py
│
├── mcps/                   # Clientes de servicios
│   ├── news_client.py
│   ├── tavily_client.py
│   ├── tts_client.py
│   └── telegram_client.py
│
├── dashboard/              # Dashboard web
│   ├── app.py
│   └── templates/
│
└── audio/                  # Archivos de audio generados
```

---

## 📈 Diagramas

### Diagrama de Secuencia - Daily Podcast

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│Telegram│     │ Router │     │Reporter│     │ Writer │     │Producer│
└───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘
    │              │              │              │              │
    │ /daily       │              │              │              │
    │─────────────▶│              │              │              │
    │              │              │              │              │
    │              │ InputGuard   │              │              │
    │              │─────────────▶│              │              │
    │              │    OK ✓      │              │              │
    │              │◀─────────────│              │              │
    │              │              │              │              │
    │              │ fetch_news   │              │              │
    │              │─────────────▶│              │              │
    │              │              │ NewsAPI      │              │
    │              │              │─────────────▶│              │
    │              │              │◀─────────────│              │
    │              │  10 articles │              │              │
    │              │◀─────────────│              │              │
    │              │              │              │              │
    │              │ generate_script             │              │
    │              │─────────────────────────────▶│              │
    │              │              │              │ ScriptGuard  │
    │              │              │              │─────────────▶│
    │              │              │              │    OK ✓      │
    │              │◀─────────────────────────────│              │
    │              │   script     │              │              │
    │              │              │              │              │
    │              │ produce & send              │              │
    │              │─────────────────────────────────────────────▶
    │              │              │              │              │ TTS
    │              │              │              │              │────▶
    │              │              │              │              │◀────
    │              │              │              │              │ send
    │◀─────────────────────────────────────────────────────────────────
    │   🎙️ Audio  │              │              │              │
    │              │              │              │              │
```

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐          ┌──────────────────┐             │
│  │   Telegram Bot   │          │   Dashboard Web  │             │
│  │  (python-tg-bot) │          │     (Flask)      │             │
│  └────────┬─────────┘          └────────┬─────────┘             │
└───────────┼─────────────────────────────┼───────────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE ORQUESTACIÓN                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     LangGraph Engine                      │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │              MultiAgentGraph (StateGraph)          │  │   │
│  │  │                                                    │  │   │
│  │  │   START → Router → Reporter → Writer → Producer    │  │   │
│  │  │              ↓                    ↓                │  │   │
│  │  │           Answer ──────────────────────→ END       │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE AGENTES                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Orchestrator │ │   Reporter   │ │    Writer    │             │
│  │   (GPT-4o)   │ │ (React Agent)│ │   (GPT-4o)   │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                  │
│  ┌──────────────┐ ┌──────────────────────────────────────────┐  │
│  │   Producer   │ │              GUARDRAILS                  │  │
│  │ (React Agent)│ │  Input │ Script │ Content Validator      │  │
│  └──────────────┘ └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE HERRAMIENTAS (MCP)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐       │
│  │  News Tools    │ │   TTS Tools    │ │ Telegram Tools │       │
│  │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │       │
│  │  │ NewsAPI  │  │ │  │ Edge TTS │  │ │  │ Bot API  │  │       │
│  │  │ Tavily   │  │ │  └──────────┘  │ │  └──────────┘  │       │
│  │  └──────────┘  │ └────────────────┘ └────────────────┘       │
│  └────────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Métricas y Observabilidad

### LangSmith Integration

```yaml
langsmith:
  enabled: true
  project: "news-service"
```

El sistema está integrado con **LangSmith** para:
- Tracing de todas las llamadas LLM
- Visualización del flujo de agentes
- Debugging de errores
- Métricas de latencia y tokens

### Logging Estructurado

```python
# Formato de logs
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Ejemplos de logs del sistema:
# [Router] Mode: daily, Chat: 123456789
# [ReporterAgent] Ejecutando tarea: Obtén las 10 noticias...
# [WriterAgent] Guion generado: 547 palabras
# [ScriptGuardrail] Validación pasada: 547 palabras (~3 min)
# [ProducerAgent] Audio enviado exitosamente
```

---

## 🚀 Conclusión

**"La IA Dice"** demuestra una implementación completa de un sistema multi-agente moderno con:

1. **Arquitectura Modular**: Agentes especializados con responsabilidades claras
2. **Orquestación Robusta**: LangGraph para flujos de trabajo complejos
3. **Seguridad**: Guardrails en múltiples capas
4. **Extensibilidad**: Herramientas MCP fácilmente ampliables
5. **Observabilidad**: Integración con LangSmith y logging estructurado

El sistema está listo para producción y puede escalar añadiendo nuevos agentes, herramientas o flujos de trabajo según las necesidades del negocio.

---

*Documentación generada para el proyecto "La IA Dice" - Servicio Multi-Agente de Noticias*
