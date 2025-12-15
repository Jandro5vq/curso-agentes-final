# 🎙️ La IA Dice - Servicio de Noticias Multi-Agente

**La IA Dice** es un podcast de noticias general que cubre todos los temas de actualidad, implementado con una **arquitectura multi-agente** usando **LangGraph**, **MCPs**, **Tavily Search** y **Edge TTS** para síntesis de voz profesional. Incluye un **dashboard web minimal** para monitoreo del sistema.

> 🌍 **Cobertura completa**: Política, economía, tecnología, deportes, entretenimiento y más.

## ⚡ Inicio Rápido

### 🖥️ Windows
```powershell
# 1. Clonar y entrar al directorio
cd news_service

# 2. Activar entorno virtual (ya creado)
.\.venv\Scripts\Activate.ps1

# 3. Ejecutar servicios con ventanas separadas
python start.py

# Opcional: Solo servicio principal
python main_multiagent.py
```

### 🐧 Linux
```bash
# 1. Clonar y entrar al directorio
cd news_service

# 2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar servicios con ventanas separadas
python start.py
# O usar el script específico de Linux:
chmod +x start_linux.sh
./start_linux.sh
```

### 🪟 **Ventanas Separadas para Logs**

El script `start.py` abre **ventanas de terminal separadas** para cada servicio, permitiendo monitorear los logs individualmente:

#### **🖥️ En Windows:**
- ✅ Se abren **ventanas de consola** automáticamente
- 🤖 **Ventana 1**: News Service (agentes multi-agent + Telegram bot)
- 📊 **Ventana 2**: Dashboard Web (Flask + métricas)

#### **🐧 En Linux:**
- ✅ Se detecta automáticamente el **terminal disponible**
- 🔧 **Soporta**: gnome-terminal, konsole, xfce4-terminal, terminator, xterm, urxvt, alacritty
- 🤖 **Ventana 1**: News Service con logs en tiempo real
- 📊 **Ventana 2**: Dashboard Web con logs de Flask

#### **💡 Ventajas:**
- 📋 **Logs separados**: Cada servicio en su propia ventana
- 🔍 **Debugging fácil**: Identificar problemas específicos por servicio
- ⚡ **Monitoreo en tiempo real**: Ver actividad de agentes y web requests
- 🎛️ **Control independiente**: Detener servicios individualmente si es necesario

## 🤖 Arquitectura Multi-Agente

El sistema utiliza **4 agentes especializados** que trabajan en conjunto:

1. **🎯 OrchestratorAgent** (Maestro)
   - Coordina todo el flujo de trabajo
   - Decide qué agentes invocar y en qué orden

2. **📰 ReporterAgent** (Especialista en Noticias)
   - Obtiene noticias usando herramientas MCP
   - Tools: `fetch_general_news_tool`, `fetch_topic_news_tool`, `search_web_news_tool`

3. **🎭 MultiPerspectiveAgent** (Especialista en Análisis Crítico) ⭐ **NUEVO**
   - Analiza noticias desde 4 perspectivas contrastadas
   - 🔴 Perspectiva Progresista/Social
   - 🔵 Perspectiva Conservadora/Mercado
   - 🟢 Perspectiva Técnica/Experto
   - 🟡 Perspectiva Internacional/Comparativa

4. **✍️ WriterAgent** (Especialista en Guiones)
   - Transforma noticias + perspectivas en guiones para podcast
   - Usa LLM directo (sin tools externos)
   - Integra análisis multiangular en la narrativa

5. **🎧 ProducerAgent** (Especialista en Producción)
   - Genera audio con TTS y envía por Telegram
   - Usa voces diferentes para cada perspectiva
   - Tools: `synthesize_speech_tool`, `send_telegram_audio_tool`, `send_telegram_message_tool`

## 🎯 Funcionalidades

### 📻 **Daily** (~3-5 minutos)
- Resumen completo de las noticias más importantes
- Cobertura balanceada de todos los temas
- Generación automática programada
- Audio profesional con Edge TTS
- Comando: Se ejecuta automáticamente a las 08:00 (configurable)

### 💊 **Píldoras Temáticas** (~1-2 minutos)
- Mini-podcasts enfocados en temas específicos
- Análisis rápido y directo
- Comando: `/podcast <tema>`
- Ejemplos: `/podcast inteligencia artificial`, `/podcast Tesla`

### 🎭 **Debates - Perspectivas Múltiples** (~5-7 minutos) ⭐ **NUEVO**
- Análisis desde 4 perspectivas diferentes
- Perspectivas balanceadas sin sesgo
- 4 voces TTS distintivas
- Comando: `/debate <tema>`
- Ejemplos: `/debate cambio climático`, `/debate impuestos`, `/debate energía nuclear`
- Perspectivas incluidas:
  - 🔴 Progresista/Social
  - 🔵 Conservadora/Mercado
  - 🟢 Técnica/Experto
  - 🟡 Internacional/Comparativa


## 📁 Estructura del Proyecto (Limpia)

```
news_service/
├── main_multiagent.py         # 🚀 Punto de entrada principal
├── config.yaml                # ⚙️ Configuración del servicio
├── scheduler.py               # ⏰ Programador de tareas
├── requirements.txt           # 📦 Dependencias Python
├── .env                       # 🔐 Variables de entorno
├──
├── agents/                    # 🤖 Agentes especializados
│   ├── __init__.py
│   ├── orchestrator.py        #   🎯 Agente maestro coordinador
│   ├── reporter.py            #   📰 Agente de noticias
│   ├── multi_perspective.py   #   🎭 Agente de perspectivas múltiples ⭐ NUEVO
│   ├── writer.py              #   ✍️ Agente generador de guiones
│   └── producer.py            #   🎧 Agente de producción y envío
├──
├── graph/                     # 📊 LangGraph Multi-Agente
│   ├── __init__.py
│   ├── multiagent_graph.py    #   📈 Definición del grafo (actualizado)
│   └── multiagent_state.py    #   💾 Estado compartido (actualizado)
├──
├── mcps/                      # 🔌 Clientes MCP
│   ├── __init__.py
│   ├── news_client.py         #   📡 Cliente de noticias
│   ├── telegram_client.py     #   📱 Cliente de Telegram
│   └── tts_client.py          #   🔊 Cliente de TTS
├──
├── tools/                     # 🛠️ Herramientas MCP
│   ├── __init__.py
│   ├── news_tools.py          #   📰 Tools de noticias
│   ├── telegram_tools.py      #   📱 Tools de Telegram
│   └── tts_tools.py           #   🔊 Tools de TTS
├──
├── persistence/               # 💾 Almacenamiento
│   ├── __init__.py
│   └── sqlite.py              #   🗄️ Base de datos SQLite
├──
├── audio/                     # 🎵 Archivos de audio generados
├── data/                      # 📊 Base de datos
├── IMPLEMENTACION_PERSPECTIVAS.md  # 📖 Documentación de perspectivas
└── README.md                  # 📖 Esta documentación
```

## 🔄 Flujo Multi-Agente (LangGraph) - Actualizado

### Daily (`/news`) - Flujo simple:
```
Router → Reporter → Writer → Producer → Finalize
```

### Píldora (`/podcast`) - Flujo simple:
```
Router → Reporter → Writer → Producer → Finalize
```

### Debate (`/debate`) ⭐ - Flujo con perspectivas:
```
Router → Reporter → MultiPerspective → Writer → Producer → Finalize
                    (4 perspectivas)
```

### Pregunta o mensaje - Flujo directo:
```
Router → Reporter → Answer → Finalize
```

**Resumen**: Las perspectivas múltiples se activan **solo** con `/debate`, manteniendo la simplicidad de daily y píldoras.

````
                    ┌─────────────────┐
                    │      START      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     ROUTER      │  ← Punto de entrada
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    REPORTER     │  ← 📰 Obtiene noticias
                    │   🤖 + Tools    │     (fetch_news_tools)
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       [question]      [daily/mini]    [default]
              │              │              │
              ▼              ▼              │
    ┌─────────────┐ ┌─────────────────┐     │
    │   ANSWER    │ │     WRITER      │     │
    │ 🤖 + Tools  │ │   🤖 LLM Solo   │     │
    └──────┬──────┘ └────────┬────────┘     │
           │                 │              │
           │                 ▼              │
           │        ┌─────────────────┐     │
           │        │    PRODUCER     │     │
           │        │   🤖 + Tools    │     │
           │        └────────┬────────┘     │
           │                 │              │
           └─────────────────┼──────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    FINALIZE     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │       END       │
                    └─────────────────┘
```

### 🛠️ **Tools MCP por Agente:**

- **📰 ReporterAgent**: `fetch_general_news_tool`, `fetch_topic_news_tool`
- **🎧 ProducerAgent**: `synthesize_speech_tool`, `send_telegram_audio_tool`, `send_telegram_message_tool`
- **❓ AnswerAgent**: `send_telegram_message_tool` (respuestas texto)

## 🛠️ Instalación

```powershell
# El proyecto ya está configurado y listo
cd news_service

# Activar el entorno virtual existente
.\.venv\Scripts\Activate.ps1

# Ejecutar el servicio
python main_multiagent.py
```

## 📱 Comandos de Telegram

| Comando | Descripción | Agentes Involucrados |
|---------|-------------|---------------------|
| `/start` | Muestra la bienvenida al podcast | - |
| `/news` | **Daily**: Resumen completo (~3 min) | Reporter → Writer → Producer |
| `/podcast <tema>` | **Píldora**: Mini-podcast temático (~1 min) | Reporter → Writer → Producer |
| `/status` | Estado del sistema multi-agente | - |
| `/graph` | Muestra la arquitectura del grafo | - |
| `<pregunta>` | **Pregunta**: Respuesta en texto | Reporter → Answer |

### 💡 **Ejemplos de Píldoras:**
- `/podcast inteligencia artificial`
- `/podcast política española`
- `/podcast economía`
- `/podcast deportes`

## 📊 Dashboard Web

El sistema incluye un **dashboard web minimal** para monitorear el servicio en tiempo real:

### 🚀 Iniciando el Dashboard

```powershell
# Desde el directorio del proyecto
python start_dashboard.py
```

El dashboard estará disponible en: **http://localhost:5000**

### 📋 Funcionalidades del Dashboard

- **📈 Estadísticas en Tiempo Real**
  - Total de conversaciones
  - Actividad en las últimas 24 horas
  - Estados del sistema

- **📱 Conversaciones Recientes**
  - Lista de interacciones más recientes
  - Estado de cada conversación
  - Duración de las sesiones

- **🔄 Auto-actualización**
  - Datos actualizados cada 30 segundos
  - Estado del sistema en tiempo real

- **📱 Diseño Responsive**
  - Optimizado para escritorio y móvil
  - Estilo minimal y profesional

### 🎛️ Endpoints API

El dashboard expone varios endpoints para integración:

- `GET /` - Dashboard principal
- `GET /api/stats` - Estadísticas JSON
- `GET /api/conversations` - Conversaciones recientes
- `GET /health` - Health check del sistema

- `/podcast deportes`

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Requeridas
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Recomendadas
NEWSAPI_KEY=...       # https://newsapi.org/
TAVILY_API_KEY=...    # https://tavily.com (Búsqueda web)

# Dashboard Web
FLASK_SECRET_KEY=news-service-dashboard-2024
DASHBOARD_PORT=5000
FLASK_DEBUG=false

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

## 📊 Arquitectura Multi-Agente

```
┌─────────────────┐
│    Telegram     │  ← python-telegram-bot (polling)
│     (Input)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LangGraph     │  ← StateGraph Multi-Agente
│  (Orchestrator) │
└────────┬────────┘
         │
         ├──► 📰 ReporterAgent ──► News MCP Client ──► NewsAPI/GNews/RSS
         │
         ├──► ✍️ WriterAgent ────► OpenAI GPT-4o-mini (directo)
         │
         ├──► 🎧 ProducerAgent ──► TTS MCP Client ──► Edge TTS + Telegram
         │
         └──► ❓ AnswerAgent ────► Telegram MCP Client (solo texto)
```

### 🔧 **Stack Tecnológico:**
- **LangGraph**: Orquestación multi-agente con StateGraph
- **OpenAI GPT-4o-mini**: LLM para generación de contenido
- **Edge TTS**: Síntesis de voz Microsoft (es-ES-AlvaroNeural)
- **python-telegram-bot**: API de Telegram
- **APScheduler**: Programación automática
- **SQLite**: Persistencia de estado
- **MCP**: Model Context Protocol para herramientas

## 🧪 Testing

```powershell
# Verificar importaciones clave
python -c "from main_multiagent import main; print('✅ Multi-Agent system OK')"
python -c "import edge_tts; print('✅ TTS OK')"
python -c "from langchain_openai import ChatOpenAI; print('✅ OpenAI OK')"

# Ejecutar el servicio multi-agente
python main_multiagent.py
```

## 🔧 Solución de Problemas

### "Conflict: terminated by other getUpdates request"
Solo puede haber una instancia del bot corriendo. Cierra otras terminales.

### "No hay noticias disponibles"
- Verifica `NEWSAPI_KEY` en .env
- El sistema tiene fallback automático a Google News RSS

### El bot no responde
- Verifica `TELEGRAM_BOT_TOKEN` en .env
- Busca el mensaje "🎙️ SERVICIO DE NOTICIAS MULTI-AGENTE - INICIANDO" en la terminal

### Error en agentes
- Los errores se muestran en los logs con `[AgentName]`
- Cada agente tiene su propio manejo de errores y recuperación

## 🎙️ Características del Podcast

### 📻 **"La IA Dice" - Daily**
- **Duración**: ~3 minutos (500-600 palabras)
- **Formato**: Resumen completo de actualidad
- **Intro**: "Hola, bienvenidos a La IA Dice, tu resumen diario de las noticias más importantes"
- **Cobertura**: Todos los temas - política, economía, tecnología, deportes, entretenimiento
- **Horario**: Programable (default 08:00 AM)

### 💊 **Píldoras Temáticas**
- **Duración**: ~1 minuto (200-250 palabras)  
- **Formato**: Enfoque específico en un tema
- **Intro**: "Hola, bienvenidos a La IA Dice. Hoy te traemos una píldora sobre [TEMA]"
- **Uso**: `/podcast <tema específico>`

## 📄 Licencia

Proyecto académico - Curso de Agentes con IA

## 🚀 Estado del Proyecto

✅ **Completado y Funcional**
- ✅ Arquitectura multi-agente con LangGraph
- ✅ 4 agentes especializados (Orchestrator, Reporter, Writer, Producer)
- ✅ Sistema MCP con herramientas reales
- ✅ Integración Telegram completa
- ✅ TTS profesional con Edge TTS
- ✅ Persistencia de estado con SQLite
- ✅ Scheduler automático
- ✅ Manejo de errores robusto
- ✅ Proyecto limpio y optimizado

## 🤝 Contribuciones

Este proyecto implementa una **arquitectura multi-agente real** usando LangGraph. Para contribuciones:

1. **Respeta la arquitectura multi-agente establecida**
2. **No elimines el sistema de agentes especializados**
3. **Mantén el uso de herramientas MCP**
4. **Documenta cualquier cambio en los agentes**
5. **Prueba el flujo completo antes de contribuir**

### 🎯 **Estructura de Agentes (NO MODIFICAR)**
- `OrchestratorAgent`: Coordinación general
- `ReporterAgent`: Especialista en obtención de noticias  
- `WriterAgent`: Especialista en generación de contenido
- `ProducerAgent`: Especialista en producción y distribución
