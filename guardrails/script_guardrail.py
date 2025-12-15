"""
Script Guardrail - Guardrail específico para guiones de podcast
================================================================

Implementa validaciones específicas para los guiones generados
por el WriterAgent antes de pasar a producción de audio.
"""

import logging
from typing import Literal

from .content_validator import ContentValidator, ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class ScriptGuardrail:
    """
    Guardrail especializado para validar guiones de podcast.
    
    Verifica:
    - Longitud apropiada según tipo (daily ~3min, píldora ~1min)
    - Estructura correcta (apertura, contenido, cierre)
    - Ausencia de formato markdown o placeholders
    - Contenido apropiado para locución
    """
    
    # Configuración de longitud por tipo de podcast
    LENGTH_CONFIG = {
        "daily": {
            "min_words": 400,
            "max_words": 700,
            "target_words": 550,
            "min_chars": 2000,
            "max_chars": 4500,
            "duration_seconds": 180,  # ~3 minutos
        },
        "pildora": {
            "min_words": 150,
            "max_words": 300,
            "target_words": 220,
            "min_chars": 800,
            "max_chars": 2000,
            "duration_seconds": 60,  # ~1 minuto
        },
        "mini": {  # Alias para pildora
            "min_words": 150,
            "max_words": 300,
            "target_words": 220,
            "min_chars": 800,
            "max_chars": 2000,
            "duration_seconds": 60,
        },
    }
    
    # Frases obligatorias de apertura (al menos una debe estar)
    REQUIRED_OPENINGS = [
        "la ia dice",
        "bienvenid",
        "hola",
    ]
    
    # Frases obligatorias de cierre (al menos una debe estar)
    REQUIRED_CLOSINGS = [
        "hasta pronto",
        "hasta la próxima",
        "nos vemos",
        "gracias por escuchar",
        "esto ha sido",
    ]
    
    def __init__(self):
        """Inicializa el guardrail con el validador de contenido."""
        self.content_validator = ContentValidator()
        logger.info("[ScriptGuardrail] Guardrail de guiones inicializado")
    
    def validate(
        self,
        script: str,
        script_type: Literal["daily", "pildora", "mini"] = "daily"
    ) -> ValidationResult:
        """
        Valida un guion de podcast completo.
        
        Args:
            script: El guion a validar
            script_type: Tipo de podcast ("daily", "pildora", "mini")
        
        Returns:
            ValidationResult con el estado de la validación
        """
        logger.info(f"[ScriptGuardrail] Validando guion tipo '{script_type}'")
        
        if not script or not script.strip():
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message="El guion está vacío",
                details={"script_type": script_type}
            )
        
        config = self.LENGTH_CONFIG.get(script_type, self.LENGTH_CONFIG["daily"])
        issues = []
        warnings = []
        
        # 1. Validar longitud
        word_count = len(script.split())
        char_count = len(script)
        
        if word_count < config["min_words"]:
            issues.append(
                f"Guion muy corto: {word_count} palabras "
                f"(mínimo: {config['min_words']} para {script_type})"
            )
        elif word_count > config["max_words"]:
            warnings.append(
                f"Guion largo: {word_count} palabras "
                f"(máximo recomendado: {config['max_words']})"
            )
        
        # 2. Validar estructura de podcast
        script_lower = script.lower()
        
        # Verificar apertura
        has_opening = any(opening in script_lower for opening in self.REQUIRED_OPENINGS)
        if not has_opening:
            issues.append("Falta apertura del podcast (mencionar 'La IA Dice' o saludo)")
        
        # Verificar cierre
        has_closing = any(closing in script_lower for closing in self.REQUIRED_CLOSINGS)
        if not has_closing:
            warnings.append("Falta cierre del podcast (despedida)")
        
        # 3. Validar formato (sin markdown ni placeholders)
        format_result = self.content_validator.validate_script_format(script)
        if not format_result.is_passed:
            if format_result.details and "issues" in format_result.details:
                for issue in format_result.details["issues"]:
                    if "Formato no permitido" in issue:
                        issues.append(issue)
                    else:
                        warnings.append(issue)
        
        # 4. Validar contenido sensible
        sensitive_result = self.content_validator.validate_sensitive_content(script)
        if not sensitive_result.is_valid:
            issues.append(f"Contenido sensible detectado: {sensitive_result.message}")
        elif sensitive_result.status == ValidationStatus.WARNING:
            warnings.append(sensitive_result.message)
        
        # 5. Validar alucinaciones
        hallucination_result = self.content_validator.validate_hallucinations(script)
        if not hallucination_result.is_valid:
            issues.append("Se detectaron posibles alucinaciones del modelo")
        
        # Construir resultado final
        if issues:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message=f"Guion no válido: {len(issues)} problemas críticos",
                details={
                    "issues": issues,
                    "warnings": warnings,
                    "word_count": word_count,
                    "char_count": char_count,
                    "script_type": script_type,
                    "target_words": config["target_words"],
                }
            )
        
        if warnings:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Guion válido con {len(warnings)} advertencias",
                details={
                    "warnings": warnings,
                    "word_count": word_count,
                    "char_count": char_count,
                    "script_type": script_type,
                }
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message=f"Guion válido: {word_count} palabras (~{config['duration_seconds']}s)",
            details={
                "word_count": word_count,
                "char_count": char_count,
                "script_type": script_type,
                "estimated_duration_seconds": int(word_count / 2.5),  # ~150 wpm en español
            }
        )
    
    def estimate_duration(self, script: str, words_per_minute: int = 150) -> int:
        """
        Estima la duración del audio en segundos.
        
        Args:
            script: El guion
            words_per_minute: Velocidad de habla (default: 150 para español)
        
        Returns:
            Duración estimada en segundos
        """
        word_count = len(script.split())
        return int((word_count / words_per_minute) * 60)
    
    def get_recommendations(
        self, 
        script: str,
        script_type: Literal["daily", "pildora", "mini"] = "daily"
    ) -> list[str]:
        """
        Genera recomendaciones para mejorar el guion.
        
        Args:
            script: El guion a analizar
            script_type: Tipo de podcast
        
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        config = self.LENGTH_CONFIG.get(script_type, self.LENGTH_CONFIG["daily"])
        word_count = len(script.split())
        
        # Recomendaciones de longitud
        diff = word_count - config["target_words"]
        if diff > 50:
            recommendations.append(
                f"Considera reducir ~{diff} palabras para un ritmo más ágil"
            )
        elif diff < -50:
            recommendations.append(
                f"Considera añadir ~{abs(diff)} palabras para más contexto"
            )
        
        # Recomendaciones de estructura
        script_lower = script.lower()
        
        if "la ia dice" not in script_lower:
            recommendations.append(
                "Menciona 'La IA Dice' en la apertura para reforzar el branding"
            )
        
        if "..." not in script and ", " not in script:
            recommendations.append(
                "Añade pausas naturales con '...' o comas para mejorar la locución"
            )
        
        return recommendations
