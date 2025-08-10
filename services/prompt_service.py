from typing import Dict, Any, List, Optional
from services.condition_evaluator import condition_evaluator, EvaluationContext
from models.Strategy import Strategy
from schemas.strategy import EvaluableRule

class StructuredPromptGenerator:
    """Generador de prompts estructurados para el sistema de reglas evaluables"""
    
    def __init__(self):
        self.base_prompt = """
Actuás como un asistente especializado en cobranzas.
Tu misión es contactar de manera eficiente a un deudor para facilitar el pago.
No respondas como humano ni toques temas irrelevantes.
"""
    
    def generate_conversation_prompt(
        self,
        strategy: Strategy,
        debtor_data: Dict[str, Any],
        current_state: str,
        conversation_history: List[Dict[str, str]],
        is_first_message: bool = False
    ) -> str:
        """
        Genera un prompt estructurado basado en las reglas evaluables de la estrategia.
        
        Args:
            strategy: Estrategia con reglas evaluables
            debtor_data: Datos del deudor
            current_state: Estado actual del deudor
            conversation_history: Historial de conversación
            is_first_message: Si es el primer mensaje
            
        Returns:
            Prompt estructurado para enviar al modelo
        """
        # Crear contexto de evaluación
        context = self._create_evaluation_context(
            debtor_data, current_state, conversation_history
        )
        
        # Evaluar reglas aplicables
        applicable_rules = self._evaluate_applicable_rules(strategy.evaluable_rules, context)
        
        # Generar prompt estructurado
        structured_prompt = self._build_structured_prompt(
            strategy, context, applicable_rules, is_first_message
        )
        
        return structured_prompt
    
    def _create_evaluation_context(
        self,
        debtor_data: Dict[str, Any],
        current_state: str,
        conversation_history: List[Dict[str, str]]
    ) -> EvaluationContext:
        """Crea el contexto de evaluación para las reglas"""
        # Analizar contexto de conversación
        conv_analysis = condition_evaluator.analyze_conversation_context(conversation_history)
        
        return EvaluationContext(
            debtor_data=debtor_data,
            current_state=current_state,
            conversation_history=conversation_history,
            last_response_date=conv_analysis.get('last_response_date'),
            days_since_last_response=conv_analysis.get('days_since_last_response'),
            total_messages=conv_analysis.get('total_messages', 0),
            negative_responses_count=conv_analysis.get('negative_responses_count', 0)
        )
    
    def _evaluate_applicable_rules(
        self,
        rules: List[Dict[str, Any]],
        context: EvaluationContext
    ) -> List[Dict[str, Any]]:
        """Evalúa qué reglas son aplicables según el contexto"""
        applicable_rules = []
        
        for rule in rules:
            if not rule.get('enabled', True):
                continue
                
            try:
                condition = rule.get('condition', '')
                if condition_evaluator.evaluate_condition(condition, context):
                    applicable_rules.append(rule)
            except Exception as e:
                print(f"Error evaluando regla '{rule.get('name', 'Unknown')}': {e}")
                continue
        
        # Ordenar por prioridad (menor número = mayor prioridad)
        applicable_rules.sort(key=lambda x: x.get('priority', 1))
        
        return applicable_rules
    
    def _build_structured_prompt(
        self,
        strategy: Strategy,
        context: EvaluationContext,
        applicable_rules: List[Dict[str, Any]],
        is_first_message: bool
    ) -> str:
        """Construye el prompt estructurado final"""
        
        # Prompt base
        prompt_parts = [self.base_prompt]
        
        # Información del deudor
        prompt_parts.append(self._build_debtor_info_section(context))
        
        # Estado actual
        prompt_parts.append(f"ESTADO ACTUAL DEL DEUDOR: {context.current_state}")
        
        # Reglas aplicables
        if applicable_rules:
            prompt_parts.append(self._build_rules_section(applicable_rules, strategy.strict_mode))
        else:
            # No hay reglas aplicables - usar fallback
            if strategy.fallback_prompt:
                prompt_parts.append(f"INSTRUCCIONES ESPECÍFICAS: {strategy.fallback_prompt}")
            else:
                prompt_parts.append("INSTRUCCIONES ESPECÍFICAS: Usar el prompt base de la estrategia")
        
        # Prompt inicial de la estrategia (solo para primer mensaje)
        if is_first_message and strategy.initial_prompt:
            prompt_parts.append(f"PROMPT INICIAL: {strategy.initial_prompt}")
        
        # Restricciones estrictas
        if strategy.strict_mode or any(rule.get('strict', False) for rule in applicable_rules):
            prompt_parts.append(self._build_strict_restrictions_section(applicable_rules))
        
        # Instrucciones finales
        prompt_parts.append(self._build_final_instructions_section())
        
        return "\n\n".join(prompt_parts)
    
    def _build_debtor_info_section(self, context: EvaluationContext) -> str:
        """Construye la sección de información del deudor"""
        debtor = context.debtor_data
        
        info_parts = ["INFORMACIÓN DEL DEUDOR:"]
        
        # Información básica
        if 'nombre' in debtor:
            info_parts.append(f"- Nombre: {debtor['nombre']}")
        if 'deuda' in debtor:
            info_parts.append(f"- Deuda: ${debtor['deuda']:,.2f}")
        if 'ciudad' in debtor:
            info_parts.append(f"- Ciudad: {debtor['ciudad']}")
        if 'edad' in debtor:
            info_parts.append(f"- Edad: {debtor['edad']}")
        
        # Contexto de conversación
        if context.total_messages > 0:
            info_parts.append(f"- Total de mensajes: {context.total_messages}")
        if context.negative_responses_count > 0:
            info_parts.append(f"- Respuestas negativas: {context.negative_responses_count}")
        if context.days_since_last_response:
            info_parts.append(f"- Días desde última respuesta: {context.days_since_last_response}")
        
        return "\n".join(info_parts)
    
    def _build_rules_section(
        self,
        applicable_rules: List[Dict[str, Any]],
        global_strict_mode: bool
    ) -> str:
        """Construye la sección de reglas aplicables"""
        if not applicable_rules:
            return ""
        
        rules_parts = ["REGLAS APLICABLES:"]
        
        for i, rule in enumerate(applicable_rules, 1):
            name = rule.get('name', f'Regla {i}')
            response = rule.get('response', '')
            strict = rule.get('strict', False)
            
            rules_parts.append(f"{i}. {name}")
            rules_parts.append(f"   Respuesta: {response}")
            if strict:
                rules_parts.append("   [ESTRICTA - Solo esta respuesta está permitida]")
        
        # Indicar si hay modo estricto global
        if global_strict_mode:
            rules_parts.append("\n⚠️ MODO ESTRICTO GLOBAL: Solo las respuestas autorizadas están permitidas.")
        
        return "\n".join(rules_parts)
    
    def _build_strict_restrictions_section(self, applicable_rules: List[Dict[str, Any]]) -> str:
        """Construye la sección de restricciones estrictas"""
        strict_rules = [rule for rule in applicable_rules if rule.get('strict', False)]
        
        if not strict_rules:
            return ""
        
        restrictions_parts = ["RESTRICCIONES ESTRICTAS:"]
        restrictions_parts.append("⚠️ ESTÁ ABSOLUTAMENTE PROHIBIDO ofrecer cualquier cosa fuera de las siguientes opciones:")
        
        for i, rule in enumerate(strict_rules, 1):
            restrictions_parts.append(f"{i}. {rule.get('response', '')}")
        
        restrictions_parts.append("\nNO PUEDES:")
        restrictions_parts.append("- Sugerir descuentos no autorizados")
        restrictions_parts.append("- Ofrecer cuotas no especificadas")
        restrictions_parts.append("- Proponer plazos no autorizados")
        restrictions_parts.append("- Inventar condiciones de pago")
        restrictions_parts.append("- Sugerir alternativas no listadas arriba")
        
        return "\n".join(restrictions_parts)
    
    def _build_final_instructions_section(self) -> str:
        """Construye las instrucciones finales"""
        return """
INSTRUCCIONES FINALES:
- Responde de manera profesional y empática
- Mantén el enfoque en la cobranza
- Si no hay reglas aplicables, usa el prompt base de la estrategia
- NO inventes descuentos, cuotas o condiciones no autorizadas
- Si el cliente pregunta por opciones no autorizadas, explica amablemente que no están disponibles
"""

# Instancia global del generador
structured_prompt_generator = StructuredPromptGenerator() 