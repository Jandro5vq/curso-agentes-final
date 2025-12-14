# 📖 Guía de Usuario - Bot de Noticias

Esta guía explica cómo usar el bot de Telegram para recibir noticias en formato de podcast.

---

## 🎯 Comandos Principales

### `/start`
**Descripción**: Inicia la conversación con el bot y muestra el mensaje de bienvenida.

**Ejemplo de respuesta**:
```
🎙️ ¡Bienvenido al servicio de noticias!

Soy un agente de IA que te mantendrá informado con podcasts 
personalizados sobre las noticias más relevantes del día.

📰 Comandos disponibles:
• /news - Recibir el podcast del día (~3 min)
• /podcast - Mini-podcast rápido (~1 min)
• /status - Ver estado del servicio

También puedes preguntarme sobre cualquier tema y te daré 
las últimas noticias al respecto.

🔔 Recibirás un podcast automático cada día a las 8:00 AM
```

---

### `/news`
**Descripción**: Genera un podcast completo con las noticias más importantes del día.

**Duración**: ~3 minutos de audio

**Contenido típico**:
- 8-10 noticias seleccionadas
- Enfoque en noticias de España
- Resumen y análisis de cada noticia
- Transiciones fluidas entre temas

**Tiempo de generación**: 20-40 segundos

**Proceso interno**:
1. 🔍 Busca noticias de múltiples fuentes (NewsAPI, GNews, Google News)
2. 📝 La IA genera un guion coherente y bien estructurado
3. 🔊 Se convierte el guion a audio con voz natural
4. 📤 Se envía el audio a Telegram

---

### `/podcast`
**Descripción**: Genera un mini-podcast rápido con noticias destacadas.

**Duración**: ~1 minuto de audio

**Contenido**:
- 3-5 noticias principales
- Formato flash informativo
- Ideal para un vistazo rápido

**Tiempo de generación**: 10-20 segundos

---

### `/status`
**Descripción**: Muestra el estado actual del servicio.

**Información mostrada**:
```
📊 Estado del Sistema:
• 🟢 Servicio activo
• 🕐 Próximo podcast: 08:00 AM
• 📰 Fuentes: NewsAPI, GNews, Google News
• 🎙️ Voz: es-ES-AlvaroNeural
```

---

## 💬 Preguntas en Lenguaje Natural

Además de los comandos, puedes hacer preguntas directamente:

### Ejemplos:

| Pregunta | Resultado |
|----------|-----------|
| "¿Qué noticias hay de fútbol?" | Noticias deportivas recientes |
| "Dame noticias de tecnología" | Últimas novedades tech |
| "¿Qué pasó con la economía española?" | Noticias económicas de España |
| "Resumen de política" | Noticias políticas actuales |
| "¿Qué hay sobre inteligencia artificial?" | Noticias sobre IA |

### Cómo funciona:
1. Envías tu pregunta
2. El bot busca noticias relacionadas con el tema
3. Genera una respuesta en texto con las noticias encontradas
4. (No genera audio para preguntas, solo para comandos)

---

## 🔔 Podcast Automático Diario

El bot envía automáticamente un podcast cada día a las **8:00 AM** (hora de España).

### Características:
- 📰 Noticias frescas del día
- 🎙️ Audio de ~3 minutos
- 🇪🇸 Enfocado en España
- 🔄 Contenido único cada día

### Requisitos:
- Haber iniciado el bot con `/start` previamente
- No haber bloqueado al bot

---

## 🔊 Sobre el Audio

### Formato:
- **Tipo**: MP3
- **Voz**: Microsoft Edge TTS (es-ES-AlvaroNeural)
- **Idioma**: Español de España
- **Calidad**: Voz natural con entonación clara

### Tips para escuchar:
- Puedes ajustar la velocidad en Telegram (1x, 1.5x, 2x)
- Funciona offline después de descargar
- Compatible con audífonos Bluetooth

---

## 📰 Fuentes de Noticias

El bot obtiene noticias de múltiples fuentes:

### Fuentes Españolas (Prioridad):
- 📰 El País
- 📰 El Mundo
- 📰 ABC
- 📰 Marca

### Fuentes Internacionales:
- 🌐 NewsAPI (agregador global)
- 🌐 GNews (agregador alternativo)
- 🌐 Google News España

### Filtrado de noticias:
- ✅ Prioriza noticias del día actual
- ✅ Descarta noticias repetidas
- ✅ Ordena por relevancia y fecha

---

## ❓ Preguntas Frecuentes

### ¿Por qué el podcast tarda en generarse?
El sistema realiza varios pasos: buscar noticias, generar guion con IA, y convertir a audio. Todo esto toma 20-40 segundos.

### ¿Puedo cambiar el idioma?
Actualmente el servicio está configurado para español de España. Contacta al administrador para otros idiomas.

### ¿Por qué a veces el podcast es más corto?
Si hay menos noticias disponibles un día, el podcast se adapta automáticamente.

### ¿Puedo recibir el podcast a otra hora?
El horario está configurado por el administrador del sistema.

### ¿El bot guarda mis mensajes?
El bot procesa tus mensajes para responder pero no almacena historial de conversaciones permanente.

---

## 🛠️ Solución de Problemas

### El bot no responde
- Intenta enviar `/start` nuevamente
- Espera unos segundos y vuelve a intentar
- Si persiste, el servicio podría estar en mantenimiento

### El audio no se reproduce
- Asegúrate de tener conexión a internet
- Prueba descargar el audio primero
- Verifica el volumen del dispositivo

### Las noticias parecen antiguas
- El sistema prioriza noticias recientes
- En días con pocas noticias, puede incluir contenido de días anteriores
- Las noticias se filtran para mostrar las más relevantes

---

## 📱 Compatibilidad

El bot funciona en:
- ✅ Telegram iOS
- ✅ Telegram Android
- ✅ Telegram Desktop
- ✅ Telegram Web

---

## 💡 Tips de Uso

1. **Escucha matutina**: El podcast diario a las 8:00 AM es ideal para empezar el día informado
2. **Preguntas específicas**: Cuanto más específica la pregunta, mejores resultados
3. **Mini-podcast**: Usa `/podcast` cuando tengas poco tiempo
4. **Offline**: Descarga los audios para escuchar sin conexión
