from typing import Dict, Any, List
from services.rule_decision_service import rule_decision_service, RuleDecision
from models.Strategy import Strategy

class StructuredPromptService:
    """Servicio para generar prompts estructurados basados en decisiones de reglas"""
    
    def __init__(self):
        self.base_prompt = """
Actuás como un asistente especializado en cobranzas.
Tu misión es contactar de manera eficiente a un deudor para facilitar el pago.
No respondas como humano ni toques temas irrelevantes.
"""
    
    def generate_action_specific_prompt(
        self,
        strategy: Strategy,
        debtor_data: Dict[str, Any],
        current_state: str,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        is_first_message: bool = False
    ) -> Dict[str, Any]:
        """
        Genera un prompt específico para la acción decidida por las reglas.
        
        Args:
            strategy: Estrategia con reglas
            debtor_data: Datos del deudor
            current_state: Estado actual
            conversation_history: Historial de conversación
            user_message: Mensaje actual del usuario
            is_first_message: Si es el primer mensaje
            
        Returns:
            Dict con prompt estructurado y metadatos de decisión
        """
        # Evaluar reglas y tomar decisión
        decision = rule_decision_service.evaluate_and_decide(
            strategy=strategy,
            debtor_data=debtor_data,
            current_state=current_state,
            conversation_history=conversation_history,
            user_message=user_message
        )
        
        # Generar prompt específico para la acción
        structured_prompt = self._build_action_specific_prompt(
            decision, strategy, debtor_data, current_state, is_first_message
        )
        
        return {
            'prompt': structured_prompt,
            'decision': decision,
            'action_type': decision.action_type,
            'restrictions': decision.restrictions or [],
            'allowed_responses': decision.allowed_responses or []
        }
    
    def _build_action_specific_prompt(
        self,
        decision: RuleDecision,
        strategy: Strategy,
        debtor_data: Dict[str, Any],
        current_state: str,
        is_first_message: bool
    ) -> str:
        """Construye un prompt específico para la acción decidida"""
        
        prompt_parts = [self.base_prompt]
        
        # Información del deudor
        prompt_parts.append(self._build_debtor_info_section(debtor_data, current_state))
        
        # Instrucciones específicas según el tipo de acción
        action_instructions = self._get_action_instructions(decision)
        prompt_parts.append(action_instructions)
        
        # Restricciones estrictas
        if decision.restrictions:
            prompt_parts.append(self._build_restrictions_section(decision.restrictions))
        
        # Respuestas permitidas
        if decision.allowed_responses:
            prompt_parts.append(self._build_allowed_responses_section(decision.allowed_responses))
        
        # Reglas para links de pago
        prompt_parts.append(self._get_payment_link_rules(current_state))
        
        # Prompt inicial (solo para primer mensaje)
        if is_first_message and strategy.initial_prompt:
            prompt_parts.append(f"PROMPT INICIAL: {strategy.initial_prompt}")
        
        # Instrucciones finales
        prompt_parts.append(self._build_final_instructions_section(decision))
        
        return "\n\n".join(prompt_parts)
    
    def _build_debtor_info_section(self, debtor_data: Dict[str, Any], current_state: str) -> str:
        """Construye la sección de información del deudor"""
        info_parts = ["INFORMACIÓN DEL DEUDOR:"]
        
        # Información básica
        if 'nombre' in debtor_data:
            info_parts.append(f"- Nombre: {debtor_data['nombre']}")
        if 'deuda' in debtor_data:
            info_parts.append(f"- Deuda: ${debtor_data['deuda']:,.2f}")
        if 'ciudad' in debtor_data:
            info_parts.append(f"- Ciudad: {debtor_data['ciudad']}")
        if 'edad' in debtor_data:
            info_parts.append(f"- Edad: {debtor_data['edad']}")
        
        info_parts.append(f"- Estado actual: {current_state}")
        
        return "\n".join(info_parts)
    
    def _get_action_instructions(self, decision: RuleDecision) -> str:
        """Obtiene instrucciones específicas según el tipo de acción"""
        
        action_instructions = {
            'offer_discount': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es ofrecer un descuento específico al deudor.
- Usa un tono empático y profesional
- Explica claramente el descuento disponible
- No ofrezcas descuentos diferentes a los autorizados
- Enfócate en facilitar el pago con el descuento
""",
            'offer_payment_plan': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es ofrecer un plan de pago específico al deudor.
- Explica las condiciones del plan de pago
- Sé claro sobre cuotas y plazos
- No inventes condiciones no autorizadas
- Enfócate en hacer el pago más accesible
""",
            'escalate_human': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es derivar el caso a un agente humano.
- Explica amablemente que un especialista se pondrá en contacto
- No intentes resolver el problema tú mismo
- Mantén un tono profesional y empático
- Asegúrate de que el cliente sepa que será contactado
""",
            'close_case': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es cerrar el caso de manera profesional.
- Explica que el caso se dará por cerrado
- Mantén un tono respetuoso
- No ofrezcas más opciones de pago
- Cierra la conversación de manera apropiada
""",
            'retry_later': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es programar un nuevo intento más tarde.
- Explica que se contactará nuevamente en el futuro
- No insistas en el pago inmediato
- Mantén un tono profesional
- Cierra la conversación temporalmente
""",
            'strict_response': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es dar una respuesta específica y estricta.
- Usa EXACTAMENTE las palabras autorizadas
- No modifiques ni agregues información
- Mantén el tono profesional
- No inventes alternativas
""",
            'fallback': """
INSTRUCCIONES ESPECÍFICAS:
Tu tarea es responder de manera genérica pero profesional.
- Usa un tono empático y respetuoso
- No ofrezcas descuentos o condiciones no autorizadas
- Enfócate en facilitar la comunicación
- Si no tienes información específica, sé honesto
"""
        }
        
        return action_instructions.get(decision.action_type, action_instructions['fallback'])
    
    def _build_restrictions_section(self, restrictions: List[str]) -> str:
        """Construye la sección de restricciones"""
        if not restrictions:
            return ""
        
        restrictions_parts = ["RESTRICCIONES ESTRICTAS:"]
        restrictions_parts.append("⚠️ ESTÁ ABSOLUTAMENTE PROHIBIDO:")
        
        for restriction in restrictions:
            restrictions_parts.append(f"- {restriction}")
        
        restrictions_parts.append("\nNO PUEDES:")
        restrictions_parts.append("- Sugerir descuentos no autorizados")
        restrictions_parts.append("- Ofrecer cuotas no especificadas")
        restrictions_parts.append("- Proponer plazos no autorizados")
        restrictions_parts.append("- Inventar condiciones de pago")
        restrictions_parts.append("- Sugerir alternativas no listadas arriba")
        
        return "\n".join(restrictions_parts)
    
    def _build_allowed_responses_section(self, allowed_responses: List[str]) -> str:
        """Construye la sección de respuestas permitidas"""
        if not allowed_responses:
            return ""
        
        responses_parts = ["RESPUESTAS AUTORIZADAS:"]
        responses_parts.append("Solo puedes usar estas respuestas o variaciones de ellas:")
        
        for i, response in enumerate(allowed_responses, 1):
            responses_parts.append(f"{i}. {response}")
        
        responses_parts.append("\nPuedes adaptar estas respuestas pero mantén la esencia del mensaje.")
        
        return "\n".join(responses_parts)
    
    def _build_final_instructions_section(self, decision: RuleDecision) -> str:
        """Construye las instrucciones finales según la decisión"""
        
        base_instructions = """
INSTRUCCIONES FINALES:
- Responde de manera profesional y empática
- Mantén el enfoque en la cobranza
- NO inventes descuentos, cuotas o condiciones no autorizadas
- Si el cliente pregunta por opciones no autorizadas, explica amablemente que no están disponibles
"""
        
        # Agregar instrucciones específicas según el tipo de acción
        if decision.action_type == 'strict_response':
            base_instructions += """
- IMPORTANTE: Usa EXACTAMENTE las palabras autorizadas
- No modifiques ni agregues información no autorizada
- Si no tienes una respuesta autorizada, sé honesto
"""
        elif decision.action_type == 'escalate_human':
            base_instructions += """
- NO intentes resolver el problema tú mismo
- Enfócate en derivar a un humano de manera profesional
- No ofrezcas soluciones alternativas
"""
        elif decision.action_type == 'fallback':
            base_instructions += """
- Si no tienes información específica, sé honesto
- Enfócate en mantener una comunicación profesional
- No inventes información o condiciones
"""
        
        return base_instructions
    
    def _get_payment_link_rules(self, current_state: str) -> str:
        """Obtiene las reglas específicas para links de pago según el estado"""
        
        rules = f"""
REGLAS PARA LINKS DE PAGO (Estado: {current_state}):

🧩 Reglas clave:
1. NUNCA generes un link de pago si el deudor no validó su identidad (DNI, email, u otros datos requeridos).
2. Si el deudor está en estado VERDE y solicita el link de pago, generá el link inmediatamente. Agradecé su disposición y mencioná que el link vence en 48 horas.
3. Si el deudor está en estado AMARILLO, sólo generá el link si lo solicita explícitamente. Si no lo pide, ofrecéselo cordialmente con frases como "¿Querés que te envíe el link para pagar?"
4. Si el deudor está en estado ROJO o GRIS, no generes el link automáticamente. Respondé con amabilidad, pero no avances sin intervención humana.
5. En todos los casos, priorizá la cordialidad, la claridad y evitá insistencias excesivas.

🗣 Frases sugeridas:
- "Claro, puedo generarte un link de pago inmediato. Tené en cuenta que vence en 48 hs."
- "¿Querés que te lo envíe ahora mismo por este medio?"
- "Gracias por tu predisposición. Enseguida te comparto el link para regularizar la deuda."
- "Entiendo tu situación. ¿Querés que te envíe el link con el descuento vigente?"

🎯 Objetivo:
Convertir conversaciones en pagos, manteniendo siempre una relación respetuosa, humana y orientada a resultados. Si detectás evasión o falta de compromiso, no avances. Escalá el caso si es necesario.
"""
        
        return rules

# Instancia global del servicio
structured_prompt_service = StructuredPromptService() 