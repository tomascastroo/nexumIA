from typing import Optional, Dict, List, Any, Literal, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime

# ============================================================================
# NUEVO SISTEMA DE REGLAS EVALUABLES
# ============================================================================

class EvaluableRule(BaseModel):
    """Regla evaluable con condición, respuesta y configuración de estrictez"""
    name: str = Field(..., description="Nombre descriptivo de la regla")
    condition: str = Field(..., description="Condición evaluable (ej: 'debt == 40000 and state == \"ROJO\"')")
    response: str = Field(..., description="Respuesta predefinida del bot")
    strict: bool = Field(True, description="Si es True, el bot NO puede sugerir nada fuera de esta respuesta")
    priority: int = Field(1, description="Prioridad de la regla (menor número = mayor prioridad)")
    enabled: bool = Field(True, description="Si la regla está habilitada")
    
    @validator('condition')
    def validate_condition(cls, v):
        """Valida que la condición sea segura y bien formada"""
        if not v or not v.strip():
            raise ValueError("La condición no puede estar vacía")
        
        # Verificar que no contenga código peligroso
        dangerous_keywords = ['import', 'exec', 'eval', '__', 'globals', 'locals']
        for keyword in dangerous_keywords:
            if keyword in v.lower():
                raise ValueError(f"La condición no puede contener '{keyword}'")
        
        return v.strip()

class EvaluableRulesConfig(BaseModel):
    """Configuración para el sistema de reglas evaluables"""
    rules: List[EvaluableRule] = Field(default=[], description="Lista de reglas evaluables")
    strict_mode: bool = Field(False, description="Modo estricto global: solo respuestas autorizadas")
    fallback_prompt: str = Field("", description="Prompt de fallback cuando no se cumplen reglas")
    
    @validator('rules')
    def validate_rules(cls, v):
        """Valida que las reglas tengan nombres únicos"""
        names = [rule.name for rule in v]
        if len(names) != len(set(names)):
            raise ValueError("Los nombres de las reglas deben ser únicos")
        return v

# ============================================================================
# SISTEMA LEGACY (mantener compatibilidad)
# ============================================================================

# Operadores para condiciones
OperatorType = Literal[">", "<", "=", "!=", ">=", "<="]
StringOperatorType = Literal["igual a", "diferente de"]
DateOperatorType = Literal["antes de", "después de"]

# Tipos de campos para condiciones
FieldType = Literal["deuda", "ciudad", "sexo", "edad", "fecha_registro", "estado_actual"]

# Estructura para una condición individual
class Condition(BaseModel):
    field: FieldType = Field(..., description="Campo a evaluar")
    operator: Union[OperatorType, StringOperatorType, DateOperatorType] = Field(..., description="Operador de comparación")
    value: Any = Field(..., description="Valor a comparar")
    
# Estructura para un grupo de condiciones (AND/OR)
class ConditionGroup(BaseModel):
    operator: Literal["AND", "OR"] = Field(..., description="Operador lógico para combinar condiciones")
    conditions: List[Union["Condition", "ConditionGroup"]] = Field(..., description="Lista de condiciones o grupos de condiciones")

# Actualizar ConditionGroup para permitir referencias circulares
ConditionGroup.model_rebuild()

# Estructura para una regla condicional avanzada
class AdvancedConditionalRule(BaseModel):
    name: str = Field(..., description="Nombre descriptivo de la regla")
    conditions: ConditionGroup = Field(..., description="Grupo de condiciones a evaluar")
    response: str = Field(..., description="Respuesta del bot si las condiciones son verdaderas")
    retry_in_days: Optional[int] = Field(None, description="Número de días para reintentar el contacto")
    escalate_to_human: bool = Field(False, description="Indica si debe escalar a un agente humano")
    close_case: bool = Field(False, description="Indica si el caso debe marcarse como cerrado")
    priority: int = Field(1, description="Prioridad de la regla (menor número = mayor prioridad)")

# Esquema para una condición individual dentro de una regla (mantener compatibilidad)
class ConditionalRule(BaseModel):
    condition: str = Field(..., description="La condición a evaluar (e.g., \"deuda < 10000\").")
    response: str = Field(..., description="La respuesta del bot si la condición es verdadera.")
    retry_in_days: Optional[int] = Field(None, description="Número de días para reintentar el contacto. Null si no hay reintento.")
    close_case: bool = Field(False, description="Indica si el caso del deudor debe marcarse como cerrado.")
    escalate_to_human: bool = Field(False, description="Indica si la conversación debe escalar a un agente humano.")

# Esquema para las reglas asociadas a un estado específico (ej. VERDE, ROJO)
class StateRules(BaseModel):
    prompt: Optional[str] = Field(None, description="Prompt específico para este estado.")
    rules: List[ConditionalRule] = Field([], description="Lista de reglas condicionales para este estado.")
    advanced_rules: List[AdvancedConditionalRule] = Field([], description="Lista de reglas condicionales avanzadas para este estado.")

# ============================================================================
# ESQUEMAS PRINCIPALES
# ============================================================================

# Esquema base para la estrategia
class StrategyBase(BaseModel):
    name: str = Field(..., description="Nombre de la estrategia.")
    initial_prompt: str = Field(..., description="Prompt inicial para la primera interacción del bot.")
    
    # Nuevo sistema de reglas evaluables
    evaluable_rules: List[EvaluableRule] = Field(
        default=[], 
        description="Reglas evaluables con condiciones, respuestas y flags de estrictez"
    )
    strict_mode: bool = Field(False, description="Modo estricto global: solo respuestas autorizadas")
    fallback_prompt: str = Field("", description="Prompt de fallback cuando no se cumplen reglas")
    
    # Sistema legacy (mantener compatibilidad)
    rules_by_state: Dict[str, StateRules] = Field(
        default={}, 
        description="Reglas de conversación organizadas por estado del deudor (legacy)."
    )

# Esquema para crear una estrategia (hereda de StrategyBase)
class StrategyCreate(StrategyBase):
    pass

# Esquema para actualizar una estrategia (todos los campos son opcionales)
class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    initial_prompt: Optional[str] = None
    evaluable_rules: Optional[List[EvaluableRule]] = None
    strict_mode: Optional[bool] = None
    fallback_prompt: Optional[str] = None
    rules_by_state: Optional[Dict[str, StateRules]] = None

# Esquema para la respuesta de la estrategia (incluye ID y fechas)
class Strategy(StrategyBase):
    id: int = Field(..., description="ID de la estrategia.")
    user_id: int = Field(..., description="ID del usuario al que pertenece la estrategia.")
    created_at: datetime = Field(..., description="Fecha y hora de creación de la estrategia.")
    updated_at: datetime = Field(..., description="Fecha y hora de la última actualización de la estrategia.")

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# PROMPTS Y CONFIGURACIÓN
# ============================================================================

# Prompt fijo (que me vas a proporcionar)
BASE_PROMPT = """
Actuás como un asistente especializado en cobranzas.
Tu misión es contactar de manera eficiente a un deudor para facilitar el pago.
No respondas como humano ni toques temas irrelevantes.
"""

# Combinación
def build_system_prompt(strategy_initial_prompt: str) -> str:
    return f"{BASE_PROMPT}\n\n{strategy_initial_prompt}"


class StrategyOut(BaseModel):
    id: int
    name: str
    initial_prompt: str
    rules_by_state: Dict[str, Any]
    evaluable_rules: List[Any]
    strict_mode: bool
    fallback_prompt: Optional[str] = None
    user_id: int

    model_config = {"from_attributes": True}


class StrategyRead(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
