"""
Agentes - Sistema Multi-Agente con Tool Calling
================================================

Este módulo define los agentes especializados del sistema:

1. OrchestratorAgent (Maestro): Coordina todo el flujo
2. ReporterAgent: Especialista en obtención de noticias
3. WriterAgent: Especialista en generación de guiones
4. ProducerAgent: Especialista en producción de audio y envío
5. MultiPerspectiveAgent: Analiza noticias desde múltiples ángulos
"""

from .orchestrator import OrchestratorAgent, create_orchestrator_agent
from .reporter import ReporterAgent, create_reporter_agent
from .writer import WriterAgent, create_writer_agent
from .producer import ProducerAgent, create_producer_agent
from .multi_perspective import MultiPerspectiveAgent, PerspectiveVoiceAssignment

__all__ = [
    "OrchestratorAgent",
    "ReporterAgent", 
    "WriterAgent",
    "ProducerAgent",
    "MultiPerspectiveAgent",
    "PerspectiveVoiceAssignment",
    "create_orchestrator_agent",
    "create_reporter_agent",
    "create_writer_agent",
    "create_producer_agent",
]
