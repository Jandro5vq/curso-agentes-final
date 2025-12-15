#!/usr/bin/env python3
"""
Script de test para el MultiPerspectiveAgent
==============================================

Demuestra cómo el nuevo agente analiza noticias desde múltiples
perspectivas contrastadas.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from agents.multi_perspective import MultiPerspectiveAgent, PerspectiveVoiceAssignment


async def test_multi_perspective():
    """Test del MultiPerspectiveAgent."""
    
    # Crear agente
    agent = MultiPerspectiveAgent()
    
    # Noticia de prueba
    news = """
    El gobierno anuncia nueva ley climática ambiciosa que reducirá 
    las emisiones de carbono en un 50% antes de 2030. La medida incluye 
    prohibición de vehículos de combustión, energía 100% renovable y 
    multas a industrias contaminantes.
    """
    
    print("\n" + "="*100)
    print("🎭 ANÁLISIS DE PERSPECTIVAS MÚLTIPLES")
    print("="*100)
    
    print(f"\n📰 NOTICIA ORIGINAL:")
    print(f"{'-'*100}")
    print(news.strip())
    print(f"{'-'*100}")
    
    # Analizar desde múltiples perspectivas
    print(f"\n🔄 Analizando desde 4 perspectivas diferentes...")
    perspectives = await agent.analyze_news(news)
    
    # Mostrar resultados
    perspective_labels = {
        'progressive': '🔴 PERSPECTIVA PROGRESISTA/SOCIAL',
        'conservative': '🔵 PERSPECTIVA CONSERVADORA/MERCADO',
        'expert': '🟢 PERSPECTIVA TÉCNICA/EXPERTO',
        'international': '🟡 PERSPECTIVA INTERNACIONAL/COMPARATIVA',
    }
    
    for key, label in perspective_labels.items():
        if key in perspectives:
            print(f"\n{label}")
            print(f"{'-'*100}")
            print(perspectives[key])
            
            # Mostrar voz asignada
            voice_config = PerspectiveVoiceAssignment.get_voice_for_perspective(key)
            print(f"\n🎙️ Voz TTS: {voice_config['name']}")
            print(f"   Emoción: {voice_config['emotion']}")
            print(f"   Descripción: {voice_config['description']}")
    
    # Mostrar resumen
    print(f"\n{'-'*100}")
    print(f"\n📋 RESUMEN DE PERSPECTIVAS:")
    print(f"{'-'*100}")
    if 'summary' in perspectives:
        print(perspectives['summary'])
    
    print(f"\n" + "="*100)
    print("✅ Test completado")
    print("="*100)


async def test_voice_assignment():
    """Test de asignación de voces a perspectivas."""
    
    print("\n" + "="*100)
    print("🎙️ CONFIGURACIÓN DE VOCES TTS POR PERSPECTIVA")
    print("="*100)
    
    perspectives = ['progressive', 'conservative', 'expert', 'international']
    
    for perspective in perspectives:
        voice_config = PerspectiveVoiceAssignment.get_voice_for_perspective(perspective)
        
        print(f"\n{perspective.upper()}")
        print(f"  - Voz: {voice_config['name']}")
        print(f"  - Emoción: {voice_config['emotion']}")
        print(f"  - Descripción: {voice_config['description']}")
    
    print(f"\n" + "="*100)


async def main():
    """Ejecuta los tests."""
    
    print("\n🧪 TESTS DEL AGENTE DE PERSPECTIVAS MÚLTIPLES\n")
    
    # Test 1: Asignación de voces
    await test_voice_assignment()
    
    # Test 2: Análisis de perspectivas
    await test_multi_perspective()


if __name__ == "__main__":
    asyncio.run(main())
