"""
Content Validator - Validador de contenido generado
====================================================

Valida que el contenido generado por los agentes cumpla con
los estándares de calidad y no contenga información inapropiada.
"""

import re
import logging
from typing import NamedTuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Estados posibles de validación."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class ValidationResult:
    """Resultado de una validación."""
    status: ValidationStatus
    message: str
    details: dict | None = None
    
    @property
    def is_valid(self) -> bool:
        """Retorna True si la validación pasó o es warning."""
        return self.status in (ValidationStatus.PASSED, ValidationStatus.WARNING)
    
    @property
    def is_passed(self) -> bool:
        """Retorna True solo si la validación pasó completamente."""
        return self.status == ValidationStatus.PASSED


class ContentValidator:
    """
    Validador de contenido que verifica múltiples aspectos del texto generado.
    
    Implementa guardrails para:
    - Detección de contenido sensible/inapropiado
    - Validación de estructura y formato
    - Verificación de longitud apropiada
    - Detección de alucinaciones o contenido sin sentido
    """
    
    # Palabras/frases que indican contenido potencialmente problemático
    SENSITIVE_PATTERNS = [
        # Contenido violento explícito
        r'\b(matar|asesinar|ejecutar|masacre)\b',
        # Lenguaje de odio
        r'\b(odio|racista|xenófob|discrimin)\w*\b',
        # Contenido adulto explícito
        r'\b(pornograf|obscen|explicit)\w*\b',
        # Desinformación marcada
        r'\b(fake news|noticia falsa|desinformación)\b',
    ]
    
    # Frases que indican posibles alucinaciones del modelo
    HALLUCINATION_INDICATORS = [
        r'según.*(?:mi conocimiento|lo que sé|mis datos)',
        r'no tengo acceso a información actual',
        r'no puedo verificar',
        r'como modelo de lenguaje',
        r'mi última actualización',
        r'no tengo la capacidad de',
    ]
    
    # Palabras reservadas que no deben aparecer en guiones
    FORBIDDEN_IN_SCRIPTS = [
        r'\[.*?\]',  # Placeholders como [NOMBRE]
        r'\{.*?\}',  # Variables como {topic}
        r'TODO:?',
        r'FIXME',
        r'XXX',
        r'\*\*.*?\*\*',  # Markdown bold
        r'###?#?',  # Markdown headers
    ]
    
    def __init__(self):
        """Inicializa el validador compilando los patrones regex."""
        self.sensitive_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS
        ]
        self.hallucination_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.HALLUCINATION_INDICATORS
        ]
        self.forbidden_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_IN_SCRIPTS
        ]
        logger.info("[ContentValidator] Validador inicializado")
    
    def validate_all(
        self, 
        content: str, 
        content_type: str = "general",
        min_length: int = 50,
        max_length: int = 10000
    ) -> ValidationResult:
        """
        Ejecuta todas las validaciones sobre el contenido.
        
        Args:
            content: Texto a validar
            content_type: Tipo de contenido ("script", "news", "answer", "general")
            min_length: Longitud mínima aceptable
            max_length: Longitud máxima aceptable
        
        Returns:
            ValidationResult con el estado consolidado de todas las validaciones
        """
        logger.info(f"[ContentValidator] Validando contenido tipo '{content_type}' ({len(content)} chars)")
        
        validations = []
        
        # 1. Validar longitud
        length_result = self.validate_length(content, min_length, max_length)
        validations.append(("length", length_result))
        
        # 2. Validar contenido sensible
        sensitive_result = self.validate_sensitive_content(content)
        validations.append(("sensitive", sensitive_result))
        
        # 3. Validar alucinaciones
        hallucination_result = self.validate_hallucinations(content)
        validations.append(("hallucination", hallucination_result))
        
        # 4. Si es script, validar formato
        if content_type == "script":
            format_result = self.validate_script_format(content)
            validations.append(("format", format_result))
        
        # Consolidar resultados
        failed = [v for name, v in validations if v.status == ValidationStatus.FAILED]
        warnings = [v for name, v in validations if v.status == ValidationStatus.WARNING]
        
        if failed:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message=f"Validación fallida: {failed[0].message}",
                details={
                    "failed_checks": [v.message for v in failed],
                    "warnings": [v.message for v in warnings],
                }
            )
        
        if warnings:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Validación con advertencias: {len(warnings)} warnings",
                details={"warnings": [v.message for v in warnings]}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Todas las validaciones pasaron correctamente",
            details={"checks_passed": len(validations)}
        )
    
    def validate_length(
        self, 
        content: str, 
        min_length: int = 50,
        max_length: int = 10000
    ) -> ValidationResult:
        """
        Valida que el contenido tenga una longitud apropiada.
        
        Args:
            content: Texto a validar
            min_length: Longitud mínima en caracteres
            max_length: Longitud máxima en caracteres
        
        Returns:
            ValidationResult con el estado de la validación
        """
        length = len(content)
        word_count = len(content.split())
        
        if length < min_length:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message=f"Contenido muy corto: {length} chars (mínimo: {min_length})",
                details={"length": length, "word_count": word_count, "min_required": min_length}
            )
        
        if length > max_length:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Contenido muy largo: {length} chars (máximo recomendado: {max_length})",
                details={"length": length, "word_count": word_count, "max_recommended": max_length}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message=f"Longitud válida: {length} chars, {word_count} palabras",
            details={"length": length, "word_count": word_count}
        )
    
    def validate_sensitive_content(self, content: str) -> ValidationResult:
        """
        Detecta contenido potencialmente sensible o inapropiado.
        
        Args:
            content: Texto a validar
        
        Returns:
            ValidationResult indicando si se encontró contenido sensible
        """
        found_patterns = []
        
        for pattern in self.sensitive_patterns:
            matches = pattern.findall(content)
            if matches:
                found_patterns.extend(matches)
        
        if found_patterns:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Se detectó contenido sensible: {', '.join(set(found_patterns[:5]))}",
                details={"patterns_found": list(set(found_patterns))}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="No se detectó contenido sensible",
        )
    
    def validate_hallucinations(self, content: str) -> ValidationResult:
        """
        Detecta posibles alucinaciones o contenido generado sin fuentes.
        
        Args:
            content: Texto a validar
        
        Returns:
            ValidationResult indicando si se detectaron indicadores de alucinación
        """
        found_indicators = []
        
        for pattern in self.hallucination_patterns:
            matches = pattern.findall(content)
            if matches:
                found_indicators.extend(matches)
        
        if found_indicators:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message="Se detectaron posibles alucinaciones del modelo",
                details={"indicators": list(set(found_indicators))}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="No se detectaron indicadores de alucinación",
        )
    
    def validate_script_format(self, content: str) -> ValidationResult:
        """
        Valida que un guion de podcast tenga el formato correcto.
        
        Args:
            content: Guion a validar
        
        Returns:
            ValidationResult indicando si el formato es correcto
        """
        issues = []
        
        # Verificar patrones prohibidos (markdown, placeholders, etc.)
        for pattern in self.forbidden_patterns:
            matches = pattern.findall(content)
            if matches:
                issues.append(f"Formato no permitido: {matches[0]}")
        
        # Verificar que tenga estructura básica de podcast
        has_greeting = any(p in content.lower() for p in [
            "hola", "bienvenid", "buenos días", "buenas tardes"
        ])
        has_closing = any(p in content.lower() for p in [
            "hasta pronto", "hasta la próxima", "nos vemos", "gracias por"
        ])
        
        if not has_greeting:
            issues.append("Falta saludo/apertura del podcast")
        
        if not has_closing:
            issues.append("Falta despedida/cierre del podcast")
        
        if issues:
            return ValidationResult(
                status=ValidationStatus.WARNING if len(issues) <= 2 else ValidationStatus.FAILED,
                message=f"Problemas de formato: {len(issues)} issues",
                details={"issues": issues}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Formato de guion correcto",
        )
    
    def sanitize_for_tts(self, content: str) -> str:
        """
        Limpia y prepara el contenido para síntesis de voz.
        
        Args:
            content: Texto a sanitizar
        
        Returns:
            Texto limpio y optimizado para TTS
        """
        # Eliminar markdown
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)      # Italic
        content = re.sub(r'#{1,6}\s*', '', content)         # Headers
        
        # Eliminar URLs
        content = re.sub(r'https?://\S+', '', content)
        
        # Normalizar espacios
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Añadir pausas naturales
        content = content.replace('...', ', ')
        
        return content
