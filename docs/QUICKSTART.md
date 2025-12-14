# 🚀 Guía de Inicio Rápido

## Prerrequisitos

- Python 3.10 o superior
- Cuenta de OpenAI con API key
- Bot de Telegram (crear con @BotFather)
- (Opcional) Cuenta en NewsAPI.org

---

## Paso 1: Clonar y Configurar Entorno

```powershell
# Navegar al directorio
cd c:\Users\aleja\Documents\Proyects\CursoAgentes\news_service

# Crear entorno virtual
python -m venv .venv

# Activar entorno
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

---

## Paso 2: Configurar Variables de Entorno

Editar el archivo `.env`:

```bash
# Requerido: OpenAI
OPENAI_API_KEY=sk-tu-clave-aqui

# Requerido: Telegram (obtener de @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABC-tu-token-aqui

# Recomendado: NewsAPI (https://newsapi.org/register)
NEWSAPI_KEY=tu-clave-newsapi

# Opcional: GNews (https://gnews.io/)
GNEWS_KEY=tu-clave-gnews

# Opcional: LangSmith (https://smith.langchain.com/)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=tu-clave-langsmith
LANGCHAIN_PROJECT=news-service
```

---

## Paso 3: Crear Bot en Telegram

1. Abrir Telegram y buscar **@BotFather**
2. Enviar `/newbot`
3. Elegir nombre (ej: "La IA Dice")
4. Elegir username (ej: "LaIADiceBot")
5. Copiar el token y pegarlo en `.env`

### Configurar comandos del bot:

Enviar a @BotFather:
```
/setcommands
```

Seleccionar tu bot y enviar:
```
start - Iniciar el bot
news - Obtener noticias del día
podcast - Generar mini-podcast
status - Ver estado del servicio
```

---

## Paso 4: Ejecutar el Servicio

```powershell
# Asegurarse de estar en el directorio correcto
cd c:\Users\aleja\Documents\Proyects\CursoAgentes\news_service

# Activar entorno
.\.venv\Scripts\Activate.ps1

# Ejecutar
python main.py
```

Deberías ver:
```
🎙️ SERVICIO DE NOTICIAS - INICIANDO
[Scheduler] Configurado para 08:00 (Europe/Madrid)
[Main] Bot de Telegram configurado
Application started
```

---

## Paso 5: Probar el Bot

1. Abrir Telegram
2. Buscar tu bot por su username
3. Enviar `/start`
4. Probar `/news` para generar un podcast
5. Hacer una pregunta como "¿Qué noticias hay de fútbol?"

---

## Comandos Disponibles

| Comando | Descripción | Tiempo |
|---------|-------------|--------|
| `/start` | Mensaje de bienvenida | Instantáneo |
| `/news` | Podcast completo del día | ~30 segundos |
| `/podcast` | Mini-podcast rápido | ~15 segundos |
| `/status` | Estado del sistema | Instantáneo |
| *texto* | Pregunta sobre noticias | ~5 segundos |

---

## Verificar que Todo Funciona

### Test de las APIs:

```powershell
# Probar TTS
python -c "import edge_tts; print('Edge TTS OK')"

# Probar OpenAI
python -c "from langchain_openai import ChatOpenAI; print('OpenAI OK')"

# Probar News Client
python -c "from mcps.news_client import NewsClient; c = NewsClient(); print(f'News OK: {len(c.fetch_general_news())} artículos')"
```

### Logs esperados al usar /news:

```
[Telegram] /news de chat_id=XXXXXX
[Reporter] Obteniendo noticias generales
[NewsClient] NewsAPI retornó 11 artículos de España
[Writer] Guion generado: 438 palabras
[TTS] Audio generado: 938.7 KB
[TelegramClient] Audio enviado correctamente
```

---

## Problemas Comunes

### "Conflict: terminated by other getUpdates request"
- **Solución**: Solo puede haber UNA instancia del bot. Cierra otras terminales.

### "OPENAI_API_KEY no configurado"
- **Solución**: Verifica que el archivo `.env` tenga la clave correcta.

### "No se encontraron noticias"
- **Solución**: El sistema tiene fallback automático. Si persiste, verifica NEWSAPI_KEY.

### El bot no responde
- **Verificar**: ¿El token de Telegram es correcto?
- **Verificar**: ¿La terminal muestra "Application started"?

---

## Próximos Pasos

1. **Personalizar horario**: Editar `config.yaml` → `scheduler.daily_time`
2. **Cambiar voz**: Editar `config.yaml` → `tts.voice`
3. **Ver métricas**: Configurar LangSmith y ver el dashboard
4. **Desplegar**: Considerar Docker o servicio en la nube

---

## Soporte

Si encuentras problemas:

1. Revisar logs en la terminal
2. Verificar archivo `.env`
3. Asegurar que solo hay una instancia corriendo
4. Revisar el archivo `news_service.log`
