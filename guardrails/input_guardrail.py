"""
Input Guardrail - Validador de entradas del usuario
====================================================

Implementa validaciones de seguridad para las entradas del usuario
antes de ser procesadas por el sistema de agentes.
"""

import re
import logging
from typing import Literal

from .content_validator import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class InputGuardrail:
    """
    Guardrail de entrada que valida y sanitiza las solicitudes del usuario.
    
    Protege contra:
    - Prompt injection
    - Contenido malicioso
    - Entradas vacías o inválidas
    - Temas prohibidos
    """
    
    # Longitudes permitidas
    MAX_INPUT_LENGTH = 500
    MIN_INPUT_LENGTH = 2
    
    # Patrones de prompt injection
    INJECTION_PATTERNS = [
        r'ignore\s+(previous|all|above)\s+(instructions?|prompts?)',
        r'disregard\s+(previous|all|above)',
        r'forget\s+(everything|all|previous)',
        r'new\s+instruction[s]?:',
        r'system\s*:\s*',
        r'assistant\s*:\s*',
        r'<\|.*?\|>',  # Tokens especiales de modelos
        r'\[INST\]',
        r'\[/INST\]',
        r'<<SYS>>',
        r'<</SYS>>',
        r'ignore.*and\s+(do|say|write)',
        r'pretend\s+(you\s+are|to\s+be)',
        r'act\s+as\s+if',
        r'jailbreak',
        r'DAN\s+mode',
    ]
    
    # Temas prohibidos para el podcast de noticias
    PROHIBITED_TOPICS = [
        r'\b(bomba|explosivo|terroris)\w*\b',
        r'\b(drogas?|narcótic|cocaine|heroin)\w*\b',
        r'\b(pornograf|xxx|adult\s+content)\w*\b',
        r'\b(hack|exploit|malware|ransomware)\w*\b',
        r'\b(armas?\s+biológicas?|armas?\s+químicas?)\b',
    ]
    
    # Caracteres sospechosos
    SUSPICIOUS_CHARS = [
        r'[\x00-\x08\x0b\x0c\x0e-\x1f]',  # Caracteres de control
        r'[\u200b-\u200f]',  # Caracteres de ancho cero
        r'[\u2028\u2029]',  # Separadores de línea/párrafo Unicode
    ]
    
    def __init__(self):
        """Inicializa el guardrail compilando patrones."""
        self.injection_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]
        self.prohibited_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PROHIBITED_TOPICS
        ]
        self.suspicious_patterns = [
            re.compile(p) for p in self.SUSPICIOUS_CHARS
        ]
        logger.info("[InputGuardrail] Guardrail de entrada inicializado")
    
    def validate(
        self,
        user_input: str,
        input_type: Literal["topic", "question", "command"] = "topic"
    ) -> ValidationResult:
        """
        Valida una entrada del usuario.
        
        Args:
            user_input: Texto ingresado por el usuario
            input_type: Tipo de entrada esperada
        
        Returns:
            ValidationResult con el estado de la validación
        """
        logger.info(f"[InputGuardrail] Validando entrada tipo '{input_type}': {user_input[:50]}...")
        
        # 1. Validar que no esté vacío
        if not user_input or not user_input.strip():
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message="La entrada está vacía",
                details={"input_type": input_type}
            )
        
        user_input = user_input.strip()
        
        # 2. Validar longitud
        if len(user_input) < self.MIN_INPUT_LENGTH:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message=f"Entrada muy corta (mínimo {self.MIN_INPUT_LENGTH} caracteres)",
                details={"length": len(user_input)}
            )
        
        if len(user_input) > self.MAX_INPUT_LENGTH:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message=f"Entrada muy larga (máximo {self.MAX_INPUT_LENGTH} caracteres)",
                details={"length": len(user_input), "max_allowed": self.MAX_INPUT_LENGTH}
            )
        
        # 3. Detectar prompt injection
        injection_result = self._check_prompt_injection(user_input)
        if not injection_result.is_valid:
            return injection_result
        
        # 4. Detectar temas prohibidos
        prohibited_result = self._check_prohibited_topics(user_input)
        if not prohibited_result.is_valid:
            return prohibited_result
        
        # 5. Detectar caracteres sospechosos
        suspicious_result = self._check_suspicious_chars(user_input)
        if not suspicious_result.is_valid:
            return suspicious_result
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Entrada válida",
            details={
                "input_type": input_type,
                "length": len(user_input),
                "sanitized": self.sanitize(user_input)
            }
        )
    
    def _check_prompt_injection(self, text: str) -> ValidationResult:
        """Detecta intentos de prompt injection."""
        for pattern in self.injection_patterns:
            if pattern.search(text):
                logger.warning(f"[InputGuardrail] Posible prompt injection detectado")
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message="Se detectó un posible intento de manipulación",
                    details={"type": "prompt_injection"}
                )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Sin indicios de prompt injection"
        )
    
    def _check_prohibited_topics(self, text: str) -> ValidationResult:
        """Detecta temas prohibidos."""
        for pattern in self.prohibited_patterns:
            match = pattern.search(text)
            if match:
                logger.warning(f"[InputGuardrail] Tema prohibido detectado: {match.group()}")
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message="El tema solicitado no está disponible",
                    details={"type": "prohibited_topic"}
                )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Tema permitido"
        )
    
    def _check_suspicious_chars(self, text: str) -> ValidationResult:
        """Detecta caracteres sospechosos."""
        for pattern in self.suspicious_patterns:
            if pattern.search(text):
                logger.warning("[InputGuardrail] Caracteres sospechosos detectados")
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    message="Se detectaron caracteres inusuales que serán eliminados",
                    details={"type": "suspicious_chars"}
                )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Sin caracteres sospechosos"
        )
    
    def sanitize(self, user_input: str) -> str:
        """
        Sanitiza la entrada del usuario eliminando caracteres problemáticos.
        
        Args:
            user_input: Texto a sanitizar
        
        Returns:
            Texto sanitizado
        """
        result = user_input.strip()
        
        # Eliminar caracteres sospechosos
        for pattern in self.suspicious_patterns:
            result = pattern.sub('', result)
        
        # Normalizar espacios múltiples
        result = re.sub(r'\s+', ' ', result)
        
        # Eliminar caracteres de control
        result = ''.join(char for char in result if ord(char) >= 32 or char in '\n\t')
        
        return result.strip()
    
    def validate_chat_id(self, chat_id: int | str) -> ValidationResult:
        """
        Valida un chat_id de Telegram.
        
        Args:
            chat_id: ID del chat a validar
        
        Returns:
            ValidationResult con el estado de la validación
        """
        try:
            chat_id_int = int(chat_id)
            
            # Los chat_id de Telegram son números grandes pero finitos
            if chat_id_int == 0:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message="Chat ID inválido: no puede ser cero",
                )
            
            # Límite razonable para evitar overflow
            if abs(chat_id_int) > 10**15:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message="Chat ID inválido: número demasiado grande",
                )
            
            return ValidationResult(
                status=ValidationStatus.PASSED,
                message="Chat ID válido",
                details={"chat_id": chat_id_int}
            )
            
        except (ValueError, TypeError):
            return ValidationResult(
                status=ValidationStatus.FAILED,
                message="Chat ID inválido: debe ser un número",
            )
