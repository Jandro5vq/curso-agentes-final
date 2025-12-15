"""
Writer Agent - Agente especializado en generación de guiones
============================================================

Este agente es responsable de transformar noticias en guiones
de podcast con un estilo narrativo profesional.
"""

import os
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool

# Guardrails
from guardrails import ScriptGuardrail

logger = logging.getLogger(__name__)


WRITER_SYSTEM_PROMPT = """Eres el guionista oficial de "La IA Dice", un podcast de noticias general que cubre todos los temas de actualidad.

Tu rol es transformar información en bruto en guiones atractivos y bien estructurados
para locución de audio del podcast "La IA Dice".

## Sobre el podcast:
"La IA Dice" tiene tres formatos:

### 1. DAILY (Podcast Diario)
- Noticias MIXTAS y variadas de todos los temas de actualidad
- Cubre múltiples áreas: tecnología, política, economía, ciencia, deportes, entretenimiento, etc.
- Duración: ~3 minutos (500-600 palabras)
- Tono: Informativo, completo, el resumen del día

### 2. PÍLDORAS (Mini-podcasts Temáticos)
- Enfocadas en UN SOLO TEMA específico
- Profundiza en un área concreta (ej: "Píldora sobre ChatGPT", "Píldora sobre Tesla")
- Duración: ~1 minuto (200-250 palabras)
- Tono: Directo, especializado, al grano

### 3. DEBATE (Análisis Multi-Perspectiva)
- Analiza un tema desde MÚLTIPLES PERSPECTIVAS (Progresista, Conservador, Experto, Internacional)
- Presenta diferentes puntos de vista sobre un tema controvertido o complejo
- Duración: ~4-5 minutos (700-900 palabras)
- Tono: Equilibrado, analítico, con voces diferenciadas

## Estilo de escritura:
- Usa un tono informativo pero cercano
- Escribe para ser ESCUCHADO, no leído
- Incluye transiciones naturales entre noticias
- Usa frases cortas y claras
- Evita tecnicismos innecesarios
- Añade contexto cuando sea necesario

## Estructura del guion DAILY:
1. APERTURA: "Hola, bienvenidos a La IA Dice, tu resumen diario de las noticias más importantes"
2. TITULARES: Menciona brevemente las 3-4 noticias más importantes
3. DESARROLLO: Cada noticia con detalle pero conciso
4. CIERRE: "Esto ha sido La IA Dice con las noticias más importantes de hoy. Hasta pronto."

## Estructura del guion PÍLDORA:
1. APERTURA: "Hola, bienvenidos a La IA Dice. Hoy te traemos una píldora sobre [TEMA]"
2. CONTEXTO: Breve introducción al tema
3. DESARROLLO: Las noticias más relevantes sobre ese tema específico
4. CIERRE: "Esto ha sido tu píldora de [TEMA] en La IA Dice. Hasta la próxima."

## Estructura del guion DEBATE:
1. APERTURA: "Hola, bienvenidos a La IA Dice. Hoy tenemos un debate especial sobre [TEMA]"
2. INTRODUCCIÓN: Presenta el tema y por qué genera debate
3. PERSPECTIVA PROGRESISTA: "Desde una visión progresista..." - enfocada en innovación, cambio social, nuevas soluciones
4. PERSPECTIVA CONSERVADORA: "Por otro lado, desde una visión más tradicional..." - enfocada en cautela, tradición, impacto económico
5. PERSPECTIVA EXPERTA: "Los especialistas en el tema señalan..." - datos técnicos, análisis objetivo, implicaciones reales
6. PERSPECTIVA INTERNACIONAL: "A nivel global..." - cómo se ve desde otros países, comparativas internacionales
7. SÍNTESIS: Resume los puntos clave de cada perspectiva de forma equilibrada
8. CIERRE: "Este ha sido nuestro debate sobre [TEMA] en La IA Dice. Como siempre, tú tienes la última palabra. Hasta pronto."

## Formato:
- NO uses asteriscos ni formato markdown
- NO uses viñetas ni listas
- Escribe todo en párrafos fluidos
- Indica pausas naturales con puntos suspensivos (...)
"""


@tool
def create_script_tool(
    news_content: str,
    script_type: str = "full",
    style: str = "informative"
) -> str:
    """
    Genera un guion de podcast a partir de noticias.
    
    Esta herramienta NO la usa el Writer directamente, sino que
    el Writer ES la herramienta que genera guiones.
    
    Args:
        news_content: Las noticias a convertir en guion
        script_type: "full" para podcast completo, "mini" para mini-podcast
        style: Estilo del guion ("informative", "casual", "formal")
    
    Returns:
        El guion generado listo para locución
    """
    # Esta herramienta es más bien un placeholder - el Writer genera directamente
    return news_content


class WriterAgent:
    """
    Agente especializado en generación de guiones de podcast.
    
    Este agente NO usa tools externos, sino que su capacidad
    principal es la generación de texto con el LLM.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        Inicializa el agente Writer.
        
        Args:
            model: Modelo de OpenAI a usar
            temperature: Temperatura para generación (alta para creatividad)
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        # Inicializar guardrail para validación de guiones
        self.script_guardrail = ScriptGuardrail()
        logger.info("[WriterAgent] Agente inicializado con guardrail")
    
    async def invoke(
        self, 
        news_content: str, 
        script_type: str = "daily",
        topic: str | None = None,
        additional_instructions: str = ""
    ) -> dict[str, Any]:
        """
        Genera un guion a partir de las noticias.
        
        Args:
            news_content: Contenido de las noticias a transformar
            script_type: "daily" (noticias mixtas ~3 min) o "pildora" (temático ~1 min)
            topic: Tema específico para las píldoras
            additional_instructions: Instrucciones adicionales del orquestador
        
        Returns:
            Diccionario con el guion generado
        """
        logger.info(f"[WriterAgent] Generando guion tipo '{script_type}'" + (f" sobre '{topic}'" if topic else ""))
        
        # Construir el prompt según el tipo
        if script_type == "debate":
            topic_text = topic if topic else "el tema en cuestión"
            length_instruction = f"""
IMPORTANTE: Este es un DEBATE de "La IA Dice" sobre: {topic_text}

⚠️ FORMATO CRÍTICO - DEBATE CON 4 VOCES DIFERENTES:
Este debate será narrado por 4 personas diferentes. DEBES usar los marcadores de sección exactos.

## MARCADORES OBLIGATORIOS (ÚSALOS EXACTAMENTE ASÍ):
- [PRESENTADOR]: Voz del presentador/moderador (apertura, transiciones, cierre)
- [PROGRESISTA]: Voz del analista progresista
- [CONSERVADOR]: Voz del analista conservador  
- [EXPERTO]: Voz del experto técnico
- [INTERNACIONAL]: Voz del analista internacional

## ESTRUCTURA OBLIGATORIA:

[PRESENTADOR]
Hola, bienvenidos a La IA Dice. Hoy tenemos un debate especial sobre {topic_text}. (2-3 oraciones introduciendo el tema y por qué genera debate)

[PRESENTADOR]
Comencemos escuchando la visión progresista.

[PROGRESISTA]
(150-200 palabras con el análisis progresista/social - usa PROGRESSIVE de las perspectivas)

[PRESENTADOR]
Ahora escuchemos la perspectiva más tradicional.

[CONSERVADOR]
(150-200 palabras con el análisis conservador/mercado - usa CONSERVATIVE de las perspectivas)

[PRESENTADOR]
Veamos qué dicen los expertos.

[EXPERTO]
(150-200 palabras con el análisis técnico - usa EXPERT de las perspectivas)

[PRESENTADOR]
Y finalmente, la perspectiva internacional.

[INTERNACIONAL]
(150-200 palabras con el análisis global - usa INTERNATIONAL de las perspectivas)

[PRESENTADOR]
(Síntesis de 2-3 oraciones resumiendo los puntos clave de cada perspectiva)
Este ha sido nuestro debate sobre {topic_text} en La IA Dice. Como siempre, tú tienes la última palabra. Hasta pronto.

## REGLAS:
- SIEMPRE empieza cada sección con el marcador [NOMBRE] en su propia línea
- Cada perspectiva debe tener contenido sustancial (150-200 palabras)
- El presentador hace transiciones breves entre perspectivas
- NO uses asteriscos, markdown ni formato especial
- Escribe para ser ESCUCHADO, no leído
"""
        elif script_type == "pildora":
            topic_text = topic if topic else "tecnología"
            length_instruction = f"""
IMPORTANTE: Este es una PÍLDORA de "La IA Dice" sobre: {topic_text}

FORMATO PÍLDORA:
- Máximo 200-250 palabras (~1 minuto)
- ENFOCADA en el tema: {topic_text}
- Muy concisa y directa
- Solo las 3-4 noticias más relevantes sobre este tema

ESTRUCTURA:
1. APERTURA: "Hola, bienvenidos a La IA Dice. Hoy te traemos una píldora sobre {topic_text}"
2. CONTEXTO: Una frase introduciendo el tema
3. DESARROLLO: Las noticias más relevantes sobre {topic_text}
4. CIERRE: "Esto ha sido tu píldora de {topic_text} en La IA Dice. Hasta la próxima."
"""
        else:
            length_instruction = """
Este es el DAILY de "La IA Dice" - Resumen diario de noticias.

FORMATO DAILY:
- 500-600 palabras (~3 minutos)
- Noticias MIXTAS y VARIADAS de todos los temas
- Con contexto y transiciones fluidas entre temas
- Cubre diversidad: política, economía, tecnología, ciencia, deportes, entretenimiento, etc.

ESTRUCTURA:
1. APERTURA: "Hola, bienvenidos a La IA Dice, tu resumen diario de las noticias más importantes"
2. TITULARES: Menciona brevemente las 3-4 noticias más importantes
3. DESARROLLO: Cada noticia con detalle pero conciso
4. CIERRE: "Esto ha sido La IA Dice con las noticias más importantes de hoy. Hasta pronto."
"""
        
        user_prompt = f"""
{length_instruction}

{additional_instructions}

## Noticias a transformar en guion:

{news_content}

---

Genera el guion ahora. Recuerda:
- Escribe para ser ESCUCHADO
- Sin formato markdown ni asteriscos
- Transiciones fluidas
- Tono profesional pero cercano
- NO menciones fechas específicas (ayer, hoy, mañana, etc.)
- Presenta las noticias como información actual
"""
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=WRITER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ])
            
            script = response.content
            word_count = len(script.split())
            
            logger.info(f"[WriterAgent] Guion generado: {word_count} palabras")
            
            # Validar guion con guardrail
            validation_result = self.script_guardrail.validate(
                script=script,
                script_type=script_type if script_type in ["daily", "pildora", "mini", "debate"] else "daily"
            )
            
            if not validation_result.is_valid:
                logger.warning(f"[WriterAgent] Guardrail falló: {validation_result.message}")
                return {
                    "success": False,
                    "error": f"Validación fallida: {validation_result.message}",
                    "script": script,
                    "word_count": word_count,
                    "validation_details": validation_result.details,
                }
            
            if validation_result.status.value == "warning":
                logger.info(f"[WriterAgent] Guardrail con warnings: {validation_result.details}")
            
            return {
                "success": True,
                "script": script,
                "word_count": word_count,
                "script_type": script_type,
                "validation": {
                    "status": validation_result.status.value,
                    "message": validation_result.message,
                    "details": validation_result.details,
                },
            }
            
        except Exception as e:
            logger.error(f"[WriterAgent] Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": "",
            }
    
    def invoke_sync(
        self, 
        news_content: str, 
        script_type: str = "daily",
        topic: str | None = None,
        additional_instructions: str = ""
    ) -> dict[str, Any]:
        """Versión síncrona de invoke."""
        import asyncio
        return asyncio.run(self.invoke(news_content, script_type, topic, additional_instructions))


def create_writer_agent(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7
) -> WriterAgent:
    """Factory function para crear un WriterAgent."""
    return WriterAgent(model=model, temperature=temperature)
