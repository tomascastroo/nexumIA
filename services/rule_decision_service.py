from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from services.condition_evaluator import condition_evaluator, EvaluationContext
from models.Strategy import Strategy

@dataclass
class RuleDecision:
    """Resultado de la evaluación de reglas con trazabilidad"""
    action_type: str  # 'offer_discount', 'escalate_human', 'close_case', 'retry_later', 'fallback'
    action_description: str
    applicable_rules: List[Dict[str, Any]]
    triggered_rule: Optional[Dict[str, Any]] = None
    confidence_score: float = 1.0
    reasoning: str = ""
    restrictions: Optional[List[str]] = None
    allowed_responses: Optional[List[str]] = None
    fallback_reason: Optional[str] = None

class RuleDecisionService:
    """Servicio centralizado para evaluación de reglas y toma de decisiones"""
    
    def __init__(self):
        self.action_types = {
            'offer_discount': 'Ofrecer descuento específico',
            'offer_payment_plan': 'Ofrecer plan de pago',
            'escalate_human': 'Derivar a humano',
            'close_case': 'Cerrar caso',
            'retry_later': 'Reintentar más tarde',
            'fallback': 'Usar respuesta genérica',
            'strict_response': 'Respuesta estricta específica'
        }
    
    def evaluate_and_decide(
        self,
        strategy: Strategy,
        debtor_data: Dict[str, Any],
        current_state: str,
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> RuleDecision:
        """
        Evalúa las reglas y toma una decisión sobre qué acción ejecutar.
        
        Args:
            strategy: Estrategia con reglas
            debtor_data: Datos del deudor
            current_state: Estado actual
            conversation_history: Historial de conversación
            user_message: Mensaje actual del usuario
            
        Returns:
            Decisión con acción a tomar y restricciones
        """
        # Crear contexto de evaluación
        context = self._create_evaluation_context(
            debtor_data, current_state, conversation_history, user_message
        )
        
        # Evaluar reglas evaluables (globales)
        applicable_evaluable_rules = self._evaluate_evaluable_rules(
            strategy.evaluable_rules, context
        )
        
        # Evaluar reglas por estado
        applicable_state_rules = self._evaluate_state_rules(
            strategy.rules_by_state, current_state, context
        )
        
        # Combinar y priorizar reglas
        all_applicable_rules = self._combine_and_prioritize_rules(
            applicable_evaluable_rules, applicable_state_rules
        )
        
        # Tomar decisión basada en reglas aplicables
        decision = self._make_decision(all_applicable_rules, strategy, context)
        
        # Generar trazabilidad
        decision.reasoning = self._generate_reasoning(
            decision, all_applicable_rules, context
        )
        
        return decision
    
    def _create_evaluation_context(
        self,
        debtor_data: Dict[str, Any],
        current_state: str,
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> EvaluationContext:
        """Crea contexto de evaluación enriquecido"""
        conv_analysis = condition_evaluator.analyze_conversation_context(conversation_history)
        
        # Agregar análisis del mensaje actual
        # message_analysis = self._analyze_user_message(user_message)
        
        return EvaluationContext(
            debtor_data=debtor_data,
            current_state=current_state,
            conversation_history=conversation_history,
            last_response_date=conv_analysis.get('last_response_date'),
            days_since_last_response=conv_analysis.get('days_since_last_response'),
            total_messages=conv_analysis.get('total_messages', 0),
            negative_responses_count=conv_analysis.get('negative_responses_count', 0)
        )
    
    def _analyze_user_message(self, message: str) -> Dict[str, Any]:
        """Analiza el mensaje del usuario para detectar intenciones"""
        message_lower = message.lower().strip()
        
        analysis = {
            'asks_for_discount': any(word in message_lower for word in ['descuento', 'rebaja', 'oferta']),
            'asks_for_payment_plan': any(word in message_lower for word in ['cuotas', 'plazos', 'pagos']),
            'refuses_payment': any(word in message_lower for word in ['no puedo', 'no tengo', 'imposible']),
            'asks_for_debt_amount': any(word in message_lower for word in ['cuanto debo', 'monto', 'deuda']),
            'is_aggressive': any(word in message_lower for word in ['molestes', 'dejen', 'corten']),
            'is_cooperative': any(word in message_lower for word in ['si', 'ok', 'bueno', 'acepto'])
        }
        
        return analysis
    
    def _evaluate_evaluable_rules(
        self,
        evaluable_rules: List[Dict[str, Any]],
        context: EvaluationContext
    ) -> List[Dict[str, Any]]:
        """Evalúa las reglas evaluables globales"""
        applicable_rules = []
        
        for rule in evaluable_rules or []:
            if not rule.get('enabled', True):
                continue
                
            try:
                condition = rule.get('condition', '')
                if condition_evaluator.evaluate_condition(condition, context):
                    # Agregar metadatos de la regla
                    rule_with_metadata = {
                        **rule,
                        'rule_type': 'evaluable',
                        'priority': rule.get('priority', 1),
                        'strict': rule.get('strict', False)
                    }
                    applicable_rules.append(rule_with_metadata)
            except Exception as e:
                print(f"Error evaluando regla evaluable '{rule.get('name', 'Unknown')}': {e}")
                continue
        
        return applicable_rules
    
    def _evaluate_state_rules(
        self,
        rules_by_state: Dict[str, Any],
        current_state: str,
        context: EvaluationContext
    ) -> List[Dict[str, Any]]:
        """Evalúa las reglas específicas del estado actual"""
        applicable_rules = []
        
        if not rules_by_state or current_state not in rules_by_state:
            return applicable_rules
        
        state_rules = rules_by_state[current_state]
        if not state_rules:
            return applicable_rules
        
        # Evaluar reglas avanzadas del estado
        advanced_rules = state_rules.get('advanced_rules', [])
        for rule in advanced_rules:
            try:
                # Evaluar condiciones complejas
                conditions = rule.get('conditions', {})
                if self._evaluate_complex_conditions(conditions, context):
                    rule_with_metadata = {
                        **rule,
                        'rule_type': 'state_advanced',
                        'state': current_state,
                        'priority': rule.get('priority', 1),
                        'strict': rule.get('strict', False)
                    }
                    applicable_rules.append(rule_with_metadata)
            except Exception as e:
                print(f"Error evaluando regla de estado '{rule.get('name', 'Unknown')}': {e}")
                continue
        
        return applicable_rules
    
    def _evaluate_complex_conditions(
        self,
        conditions: Dict[str, Any],
        context: EvaluationContext
    ) -> bool:
        """Evalúa condiciones complejas (AND/OR)"""
        if not conditions:
            return True
        
        operator = conditions.get('operator', 'AND')
        condition_list = conditions.get('conditions', [])
        
        if not condition_list:
            return True
        
        results = []
        for condition in condition_list:
            if isinstance(condition, dict) and 'operator' in condition:
                # Condición anidada
                result = self._evaluate_complex_conditions(condition, context)
            else:
                # Condición simple
                result = self._evaluate_simple_condition(condition, context)
            results.append(result)
        
        if operator == 'AND':
            return all(results)
        elif operator == 'OR':
            return any(results)
        else:
            return False
    
    def _evaluate_simple_condition(
        self,
        condition: Dict[str, Any],
        context: EvaluationContext
    ) -> bool:
        """Evalúa una condición simple"""
        field = condition.get('field', '')
        operator = condition.get('operator', '')
        value = condition.get('value', '')
        
        if not field or not operator:
            return False
        
        # Obtener valor del campo
        field_value = self._get_field_value(field, context)
        
        # Evaluar según operador
        try:
            if operator == '==':
                return field_value == value
            elif operator == '!=':
                return field_value != value
            elif operator == '>':
                return float(field_value) > float(value)
            elif operator == '<':
                return float(field_value) < float(value)
            elif operator == '>=':
                return float(field_value) >= float(value)
            elif operator == '<=':
                return float(field_value) <= float(value)
            elif operator == 'contains':
                return str(value) in str(field_value)
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def _get_field_value(self, field: str, context: EvaluationContext) -> Any:
        """Obtiene el valor de un campo del contexto"""
        # Campos del deudor
        if field in context.debtor_data:
            return context.debtor_data[field]
        
        # Campos especiales
        field_mapping = {
            'estado': context.current_state,
            'state': context.current_state,
            'deuda': context.debtor_data.get('deuda', 0),
            'debt': context.debtor_data.get('deuda', 0),
            'total_messages': context.total_messages,
            'negative_responses_count': context.negative_responses_count,
            'days_since_last_response': context.days_since_last_response or 0
        }
        
        return field_mapping.get(field, '')
    
    def _combine_and_prioritize_rules(
        self,
        evaluable_rules: List[Dict[str, Any]],
        state_rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combina y prioriza todas las reglas aplicables"""
        all_rules = evaluable_rules + state_rules
        
        # Ordenar por prioridad (menor número = mayor prioridad)
        all_rules.sort(key=lambda x: x.get('priority', 1))
        
        # Filtrar reglas duplicadas o conflictivas
        filtered_rules = []
        seen_responses = set()
        
        for rule in all_rules:
            response = rule.get('response', '').strip()
            if response and response not in seen_responses:
                filtered_rules.append(rule)
                seen_responses.add(response)
            elif not response:
                filtered_rules.append(rule)
        
        return filtered_rules
    
    def _make_decision(
        self,
        applicable_rules: List[Dict[str, Any]],
        strategy: Strategy,
        context: EvaluationContext
    ) -> RuleDecision:
        """Toma la decisión final basada en las reglas aplicables"""
        
        if not applicable_rules:
            # No hay reglas aplicables - usar fallback
            return RuleDecision(
                action_type='fallback',
                action_description='No hay reglas aplicables',
                applicable_rules=[],
                fallback_reason='No se cumplen condiciones de ninguna regla',
                restrictions=['No inventar descuentos o condiciones'],
                allowed_responses=[strategy.fallback_prompt] if strategy.fallback_prompt else []
            )
        
        # Obtener la regla de mayor prioridad
        primary_rule = applicable_rules[0]
        
        # Determinar tipo de acción
        action_type = self._determine_action_type(primary_rule, context)
        
        # Generar restricciones y respuestas permitidas
        restrictions, allowed_responses = self._generate_restrictions_and_responses(
            applicable_rules, strategy.strict_mode
        )
        
        return RuleDecision(
            action_type=action_type,
            action_description=self.action_types.get(action_type, 'Acción no definida'),
            applicable_rules=applicable_rules,
            triggered_rule=primary_rule,
            restrictions=restrictions,
            allowed_responses=allowed_responses
        )
    
    def _determine_action_type(
        self,
        rule: Dict[str, Any],
        context: EvaluationContext
    ) -> str:
        """Determina el tipo de acción basado en la regla"""
        
        response = rule.get('response', '').lower()
        
        # Detectar tipo de acción por palabras clave
        if any(word in response for word in ['descuento', 'rebaja', '%']):
            return 'offer_discount'
        elif any(word in response for word in ['cuotas', 'plazos', 'pagos']):
            return 'offer_payment_plan'
        elif rule.get('escalate_to_human', False):
            return 'escalate_human'
        elif rule.get('close_case', False):
            return 'close_case'
        elif rule.get('retry_in_days'):
            return 'retry_later'
        elif rule.get('strict', False):
            return 'strict_response'
        else:
            return 'fallback'
    
    def _generate_restrictions_and_responses(
        self,
        applicable_rules: List[Dict[str, Any]],
        global_strict_mode: bool
    ) -> Tuple[List[str], List[str]]:
        """Genera restricciones y respuestas permitidas"""
        
        restrictions = []
        allowed_responses = []
        
        # Agregar respuestas de reglas estrictas
        strict_rules = [r for r in applicable_rules if r.get('strict', False)]
        for rule in strict_rules:
            response = rule.get('response', '').strip()
            if response:
                allowed_responses.append(response)
        
        # Si hay modo estricto global o reglas estrictas
        if global_strict_mode or strict_rules:
            restrictions.extend([
                "NO inventar descuentos no autorizados",
                "NO ofrecer cuotas no especificadas",
                "NO proponer plazos no autorizados",
                "NO inventar condiciones de pago",
                "Solo usar respuestas autorizadas"
            ])
        
        # Si no hay respuestas estrictas, agregar respuestas de todas las reglas
        if not allowed_responses:
            for rule in applicable_rules:
                response = rule.get('response', '').strip()
                if response:
                    allowed_responses.append(response)
        
        return restrictions, allowed_responses
    
    def _generate_reasoning(
        self,
        decision: RuleDecision,
        all_rules: List[Dict[str, Any]],
        context: EvaluationContext
    ) -> str:
        """Genera el razonamiento de la decisión para trazabilidad"""
        
        reasoning_parts = []
        
        if decision.triggered_rule:
            rule = decision.triggered_rule
            reasoning_parts.append(f"Regla activada: {rule.get('name', 'Sin nombre')}")
            reasoning_parts.append(f"Tipo: {rule.get('rule_type', 'Desconocido')}")
            reasoning_parts.append(f"Prioridad: {rule.get('priority', 1)}")
            reasoning_parts.append(f"Estricta: {rule.get('strict', False)}")
        
        reasoning_parts.append(f"Estado del deudor: {context.current_state}")
        reasoning_parts.append(f"Deuda: ${context.debtor_data.get('deuda', 0):,.2f}")
        reasoning_parts.append(f"Total de mensajes: {context.total_messages}")
        
        if context.negative_responses_count > 0:
            reasoning_parts.append(f"Respuestas negativas: {context.negative_responses_count}")
        
        reasoning_parts.append(f"Acción decidida: {decision.action_description}")
        
        if decision.fallback_reason:
            reasoning_parts.append(f"Motivo del fallback: {decision.fallback_reason}")
        
        return " | ".join(reasoning_parts)

# Instancia global del servicio
rule_decision_service = RuleDecisionService() 