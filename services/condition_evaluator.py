import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import ast

@dataclass
class EvaluationContext:
    """Contexto para evaluar condiciones"""
    debtor_data: Dict[str, Any]
    current_state: str
    conversation_history: List[Dict[str, str]]
    last_response_date: Optional[datetime] = None
    days_since_last_response: Optional[int] = None
    total_messages: int = 0
    negative_responses_count: int = 0

class ConditionEvaluator:
    """Evaluador de condiciones para reglas de cobranza"""
    
    def __init__(self):
        self.operators = {
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            'in': lambda x, y: x in y,
            'not in': lambda x, y: x not in y,
            'contains': lambda x, y: y in str(x),
            'starts_with': lambda x, y: str(x).startswith(str(y)),
            'ends_with': lambda x, y: str(x).endswith(str(y))
        }
    
    def evaluate_condition(self, condition: str, context: EvaluationContext) -> bool:
        """
        Evalúa una condición compleja usando el contexto del deudor.
        
        Args:
            condition: Condición en formato string (ej: "debt == 40000 and state == 'ROJO'")
            context: Contexto con datos del deudor
            
        Returns:
            True si la condición se cumple, False en caso contrario
        """
        try:
            # Normalizar la condición
            condition = self._normalize_condition(condition)
            
            # Crear variables locales para evaluación
            local_vars = self._create_evaluation_vars(context)
            
            # Evaluar la condición
            parsed = ast.parse(condition, mode='eval')
            result = eval(compile(parsed, filename="<ast>", mode="eval"), {}, local_vars)
            
            return bool(result)
        except Exception as e:
            print(f"Error evaluando condición '{condition}': {e}")
            return False
    
    def _normalize_condition(self, condition: str) -> str:
        """Normaliza la condición para evaluación segura"""
        # Reemplazar operadores de texto por funciones
        condition = re.sub(r'\bcontains\b', 'contains', condition)
        condition = re.sub(r'\bstarts_with\b', 'starts_with', condition)
        condition = re.sub(r'\bends_with\b', 'ends_with', condition)
        
        # Reemplazar operadores de comparación
        condition = re.sub(r'\b==\b', '==', condition)
        condition = re.sub(r'\b!=\b', '!=', condition)
        condition = re.sub(r'\b>=\b', '>=', condition)
        condition = re.sub(r'\b<=\b', '<=', condition)
        condition = re.sub(r'\b>\b', '>', condition)
        condition = re.sub(r'\b<\b', '<', condition)
        
        # Reemplazar operadores lógicos
        condition = re.sub(r'\band\b', 'and', condition)
        condition = re.sub(r'\bor\b', 'or', condition)
        condition = re.sub(r'\bnot\b', 'not', condition)
        
        return condition
    
    def _create_evaluation_vars(self, context: EvaluationContext) -> Dict[str, Any]:
        """Crea variables seguras para evaluación"""
        vars_dict = {
            # Datos del deudor
            'debt': self._safe_get(context.debtor_data, 'deuda', 0),
            'deuda': self._safe_get(context.debtor_data, 'deuda', 0),
            'ciudad': self._safe_get(context.debtor_data, 'ciudad', ''),
            'sexo': self._safe_get(context.debtor_data, 'sexo', ''),
            'edad': self._safe_get(context.debtor_data, 'edad', 0),
            'fecha_registro': self._safe_get(context.debtor_data, 'fecha_registro', ''),
            'estado_actual': context.current_state,
            'state': context.current_state,
            
            # Contexto de conversación
            'total_messages': context.total_messages,
            'negative_responses_count': context.negative_responses_count,
            'days_since_last_response': context.days_since_last_response or 0,
            
            # Funciones de ayuda
            'contains': lambda x, y: y in str(x),
            'starts_with': lambda x, y: str(x).startswith(str(y)),
            'ends_with': lambda x, y: str(x).endswith(str(y)),
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            
            # Constantes
            'True': True,
            'False': False,
            'None': None
        }
        
        # Agregar todos los datos del deudor como variables individuales
        for key, value in context.debtor_data.items():
            vars_dict[key] = value
        
        return vars_dict
    
    def _safe_get(self, data: Dict[str, Any], key: str, default: Any) -> Any:
        """Obtiene un valor de forma segura"""
        try:
            value = data.get(key, default)
            # Intentar convertir a número si es posible
            if isinstance(value, str) and value.replace('.', '').replace(',', '').isdigit():
                return float(value.replace(',', '.'))
            return value
        except Exception:
            return default
    
    def analyze_conversation_context(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analiza el contexto de la conversación para extraer información útil"""
        if not conversation_history:
            return {
                'total_messages': 0,
                'negative_responses_count': 0,
                'last_response_date': None,
                'days_since_last_response': None
            }
        
        total_messages = len(conversation_history)
        negative_responses_count = 0
        
        # Contar respuestas negativas
        negative_keywords = [
            'no', 'no puedo', 'no tengo', 'imposible', 'no quiero', 
            'no me interesa', 'no puedo pagar', 'no tengo dinero',
            'no puedo ahora', 'no tengo tiempo', 'no me conviene'
        ]
        
        for msg in conversation_history:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                if any(keyword in content for keyword in negative_keywords):
                    negative_responses_count += 1
        
        # Calcular días desde la última respuesta
        last_response_date = None
        days_since_last_response = None
        
        if conversation_history:
            # Buscar la última respuesta del usuario
            for msg in reversed(conversation_history):
                if msg.get('role') == 'user':
                    # Aquí podrías extraer la fecha si la tienes en el mensaje
                    # Por ahora usamos una estimación
                    last_response_date = datetime.now() - timedelta(days=1)
                    days_since_last_response = 1
                    break
        
        return {
            'total_messages': total_messages,
            'negative_responses_count': negative_responses_count,
            'last_response_date': last_response_date,
            'days_since_last_response': days_since_last_response
        }

# Instancia global del evaluador
condition_evaluator = ConditionEvaluator() 