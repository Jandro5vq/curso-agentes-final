"""
MultiPerspectiveAgent - Analiza noticias desde múltiples ángulos
================================================================

Este agente genera análisis de una noticia desde 4 perspectivas
contrastadas:
1. Progresista/Social
2. Conservadora/Mercado
3. Técnica/Experto
4. Internacional/Comparativa

Genera un podcast tipo "debate balanceado" donde cada perspectiva
se expresa de forma contrastada pero equilibrada.
"""

import asyncio
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)


# System prompts para cada perspectiva
PROGRESSIVE_PERSPECTIVE = """Eres un analista progresista/social analizando una noticia.

Tu enfoque:
- Priorizar impacto social y humano
- Considerar desigualdades y grupos vulnerables
- Favorecer soluciones colectivas y cooperativas
- Cuestionar el statu quo
- Buscar sostenibilidad ambiental y social

Sé apasionado pero argumentado. Usa datos reales.
Tu respuesta debe ser un párrafo de 150-200 palabras."""

CONSERVATIVE_PERSPECTIVE = """Eres un analista conservador/mercadista analizando una noticia.

Tu enfoque:
- Priorizar eficiencia económica y mercado libre
- Considerar impacto en negocios e inversión
- Favor iniciativa privada y emprendimiento
- Defender instituciones establecidas
- Buscar estabilidad y crecimiento económico

Sé lógico y basado en datos. Cuestiona soluciones que ves como ineficientes.
Tu respuesta debe ser un párrafo de 150-200 palabras."""

EXPERT_PERSPECTIVE = """Eres un experto técnico/especialista analizando una noticia.

Tu enfoque:
- Análisis basado en datos y evidencia científica
- Explicar mecanismos técnicos con claridad
- Identificar supuestos y riesgos técnicos
- Proponer soluciones prácticas
- Ser neutral pero riguroso

Sé accesible pero preciso. Evita jerga innecesaria.
Tu respuesta debe ser un párrafo de 150-200 palabras."""

INTERNATIONAL_PERSPECTIVE = """Eres un analista internacional comparando impactos globales.

Tu enfoque:
- Comparar con situaciones en otros países
- Analizar contexto geopolítico
- Identificar tendencias globales
- Considerar acuerdos/organismos internacionales
- Buscar lecciones de otros lugares

Sé globalmente consciente e informado. Usa ejemplos internacionales.
Tu respuesta debe ser un párrafo de 150-200 palabras."""


class MultiPerspectiveAgent:
    """
    Agente que analiza una noticia desde 4 perspectivas contrastadas.
    
    Cada perspectiva es generada por el LLM con un system prompt diferente.
    Las perspectivas están diseñadas para ser complementarias y contrastadas
    sin ser propaganda política.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.8):
        """
        Inicializa el agente de perspectivas múltiples.
        
        Args:
            model: Modelo de OpenAI a usar
            temperature: Temperatura del LLM (más alto = más creativo)
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
        )
        self.model = model
        self.temperature = temperature
        
        logger.info(f"[MultiPerspectiveAgent] Inicializado con modelo {model}")
    
    async def analyze_news(self, news: str) -> dict[str, str]:
        """
        Analiza una noticia desde 4 perspectivas diferentes.
        
        Args:
            news: Texto de la noticia a analizar
            
        Returns:
            Dict con perspectivas: {
                'progressive': str,
                'conservative': str,
                'expert': str,
                'international': str,
                'summary': str  # Resumen de contrastes
            }
        """
        
        logger.info(f"[MultiPerspectiveAgent] Analizando noticia de {len(news)} caracteres")
        
        perspectives_prompts = {
            'progressive': (PROGRESSIVE_PERSPECTIVE, "Perspectiva Progresista/Social"),
            'conservative': (CONSERVATIVE_PERSPECTIVE, "Perspectiva Conservadora/Mercado"),
            'expert': (EXPERT_PERSPECTIVE, "Perspectiva Técnica/Experto"),
            'international': (INTERNATIONAL_PERSPECTIVE, "Perspectiva Internacional"),
        }
        
        try:
            # Ejecutar análisis paralelos para cada perspectiva
            tasks = []
            for perspective_key, (system_prompt, label) in perspectives_prompts.items():
                task = self._analyze_from_perspective(
                    news, system_prompt, perspective_key, label
                )
                tasks.append(task)
            
            # Esperar todos los análisis en paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            perspectives = {}
            for (perspective_key, _), result in zip(perspectives_prompts.items(), results):
                if isinstance(result, Exception):
                    logger.error(f"Error en perspectiva {perspective_key}: {result}")
                    perspectives[perspective_key] = f"Error: {str(result)}"
                else:
                    perspectives[perspective_key] = result
                    logger.info(f"[MultiPerspectiveAgent] {perspective_key} completado")
            
            # Generar resumen de contrastes
            summary = await self._generate_summary(news, perspectives)
            perspectives['summary'] = summary
            
            logger.info(f"[MultiPerspectiveAgent] Análisis completado")
            
            return perspectives
            
        except Exception as e:
            logger.error(f"[MultiPerspectiveAgent] Error analizando noticia: {e}")
            return {
                'progressive': f"Error: {str(e)}",
                'conservative': f"Error: {str(e)}",
                'expert': f"Error: {str(e)}",
                'international': f"Error: {str(e)}",
                'summary': f"Error procesando perspectivas: {str(e)}"
            }
    
    async def _analyze_from_perspective(
        self,
        news: str,
        system_prompt: str,
        perspective_key: str,
        perspective_label: str
    ) -> str:
        """
        Analiza una noticia desde una perspectiva específica.
        
        Args:
            news: Noticia a analizar
            system_prompt: System prompt de la perspectiva
            perspective_key: Clave de la perspectiva (para logging)
            perspective_label: Etiqueta legible de la perspectiva
            
        Returns:
            Análisis de la perspectiva
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analiza esta noticia: {news}")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            analysis = response.content
            logger.debug(f"[MultiPerspectiveAgent] {perspective_label}: {len(analysis)} caracteres")
            
            return analysis
            
        except Exception as e:
            logger.error(f"[MultiPerspectiveAgent] Error en {perspective_label}: {e}")
            raise
    
    async def _generate_summary(
        self,
        news: str,
        perspectives: dict[str, str]
    ) -> str:
        """
        Genera un resumen de los puntos de acuerdo y desacuerdo entre perspectivas.
        
        Args:
            news: Noticia original
            perspectives: Dict con todas las perspectivas
            
        Returns:
            Resumen de contrastes y acuerdos
        """
        
        try:
            summary_prompt = f"""
            Dada esta noticia:
            "{news}"
            
            Y estos análisis de 4 perspectivas:
            
            PROGRESISTA: {perspectives.get('progressive', 'N/A')}
            CONSERVADORA: {perspectives.get('conservative', 'N/A')}
            EXPERTO: {perspectives.get('expert', 'N/A')}
            INTERNACIONAL: {perspectives.get('international', 'N/A')}
            
            Genera un resumen ejecutivo (200 palabras max) que destaque:
            1. Puntos de ACUERDO entre perspectivas
            2. Puntos de DESACUERDO principales
            3. ¿Cuáles son los hechos objetivos?
            4. ¿Dónde comienza la interpretación política/ideológica?
            
            Sé equilibrado y justo con todas las perspectivas.
            """
            
            messages = [
                SystemMessage(
                    content="Eres un mediador justo que resume perspectivas contrapuestas"
                ),
                HumanMessage(content=summary_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"[MultiPerspectiveAgent] Error generando resumen: {e}")
            return f"Error generando resumen: {str(e)}"


class PerspectiveVoiceAssignment:
    """
    Asigna voces TTS diferentes a cada perspectiva para crear
    un podcast tipo "debate" con voces distintivas.
    """
    
    # Mapeo de perspectivas a voces TTS
    VOICE_MAPPING = {
        'progressive': {
            'name': 'es-ES-IreneuralNeural',  # Voz joven, energética
            'emotion': 'cheerful',
            'description': 'Voz joven, empática, con energía'
        },
        'conservative': {
            'name': 'es-ES-AlvaroNeural',  # Voz profunda, seria
            'emotion': 'calm',
            'description': 'Voz profunda, seria, reflexiva'
        },
        'expert': {
            'name': 'es-ES-IsabelaNeural',  # Voz clara, profesional
            'emotion': 'calm',
            'description': 'Voz clara, profesional, objetiva'
        },
        'international': {
            'name': 'es-ES-XimenaNeural',  # Voz cálida, accesible
            'emotion': 'friendly',
            'description': 'Voz cálida, accesible, internacional'
        }
    }
    
    @staticmethod
    def get_voice_for_perspective(perspective: str) -> dict:
        """
        Obtiene la voz TTS configurada para una perspectiva.
        
        Args:
            perspective: Clave de perspectiva
            
        Returns:
            Dict con configuración de voz
        """
        return PerspectiveVoiceAssignment.VOICE_MAPPING.get(
            perspective,
            PerspectiveVoiceAssignment.VOICE_MAPPING['expert']  # Default
        )


if __name__ == "__main__":
    # Test del agente
    async def test():
        agent = MultiPerspectiveAgent()
        
        news = "El gobierno anuncia nueva ley climática ambiciosa para reducir emisiones 50% antes de 2030"
        
        perspectives = await agent.analyze_news(news)
        
        print("\n" + "="*80)
        print("ANÁLISIS DESDE MÚLTIPLES PERSPECTIVAS")
        print("="*80)
        
        for key, content in perspectives.items():
            print(f"\n{key.upper()}:")
            print("-" * 80)
            print(content)
    
    asyncio.run(test())
