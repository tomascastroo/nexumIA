import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from models.Debtor import Debtor

logger = logging.getLogger(__name__)

class DebtorState(Enum):
    # Estados base
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"
    GRIS = "GRIS"
    
    # Estados temporales
    PENDIENTE_PAGO = "PENDIENTE_PAGO"
    EN_NEGOCIACION = "EN_NEGOCIACION"
    ESCALADO_HUMANO = "ESCALADO_HUMANO"
    EN_SEGUIMIENTO = "EN_SEGUIMIENTO"
    
    # Estados compuestos
    VERDE_CON_DESCUENTO = "VERDE_CON_DESCUENTO"
    AMARILLO_NEGOCIANDO = "AMARILLO_NEGOCIANDO"
    ROJO_ESCALADO = "ROJO_ESCALADO"

@dataclass
class StateTransition:
    """Transición de estado"""
    from_state: DebtorState
    to_state: DebtorState
    trigger: str
    conditions: List[str]
    actions: List[str]
    timeout_minutes: Optional[int] = None
    auto_rollback: bool = False

@dataclass
class StateHistory:
    """Historial de cambios de estado"""
    timestamp: datetime
    from_state: str
    to_state: str
    trigger: str
    user_id: Optional[int] = None
    notes: Optional[str] = None

class StateMachineService:
    """Servicio de máquina de estados robusta para deudores"""
    
    def __init__(self):
        # Definir transiciones válidas
        self.transitions = {
            # Transiciones desde GRIS
            (DebtorState.GRIS, DebtorState.VERDE): StateTransition(
                from_state=DebtorState.GRIS,
                to_state=DebtorState.VERDE,
                trigger="payment_intent",
                conditions=["has_identity_confirmation", "positive_response"],
                actions=["generate_payment_link", "update_contact_schedule"],
                timeout_minutes=60
            ),
            
            (DebtorState.GRIS, DebtorState.AMARILLO): StateTransition(
                from_state=DebtorState.GRIS,
                to_state=DebtorState.AMARILLO,
                trigger="negotiation_start",
                conditions=["has_identity_confirmation", "asks_for_discount"],
                actions=["offer_discount", "schedule_followup"],
                timeout_minutes=120
            ),
            
            (DebtorState.GRIS, DebtorState.ROJO): StateTransition(
                from_state=DebtorState.GRIS,
                to_state=DebtorState.ROJO,
                trigger="negative_response",
                conditions=["refuses_payment", "aggressive_behavior"],
                actions=["escalate_to_human", "log_negative_interaction"],
                auto_rollback=True
            ),
            
            # Transiciones desde VERDE
            (DebtorState.VERDE, DebtorState.VERDE_CON_DESCUENTO): StateTransition(
                from_state=DebtorState.VERDE,
                to_state=DebtorState.VERDE_CON_DESCUENTO,
                trigger="discount_offered",
                conditions=["payment_intent", "discount_accepted"],
                actions=["apply_discount", "generate_payment_link"],
                timeout_minutes=30
            ),
            
            (DebtorState.VERDE, DebtorState.PENDIENTE_PAGO): StateTransition(
                from_state=DebtorState.VERDE,
                to_state=DebtorState.PENDIENTE_PAGO,
                trigger="payment_link_sent",
                conditions=["payment_link_generated"],
                actions=["schedule_payment_reminder"],
                timeout_minutes=2880  # 48 horas
            ),
            
            # Transiciones desde AMARILLO
            (DebtorState.AMARILLO, DebtorState.AMARILLO_NEGOCIANDO): StateTransition(
                from_state=DebtorState.AMARILLO,
                to_state=DebtorState.AMARILLO_NEGOCIANDO,
                trigger="negotiation_active",
                conditions=["discount_requested", "payment_plan_discussed"],
                actions=["offer_payment_plan", "schedule_negotiation_followup"],
                timeout_minutes=1440  # 24 horas
            ),
            
            (DebtorState.AMARILLO, DebtorState.EN_NEGOCIACION): StateTransition(
                from_state=DebtorState.AMARILLO,
                to_state=DebtorState.EN_NEGOCIACION,
                trigger="negotiation_started",
                conditions=["counter_offer_made"],
                actions=["evaluate_counter_offer", "schedule_response"],
                timeout_minutes=720  # 12 horas
            ),
            
            # Transiciones desde ROJO
            (DebtorState.ROJO, DebtorState.ROJO_ESCALADO): StateTransition(
                from_state=DebtorState.ROJO,
                to_state=DebtorState.ROJO_ESCALADO,
                trigger="human_intervention",
                conditions=["escalation_required"],
                actions=["assign_to_human", "log_escalation"],
                timeout_minutes=1440  # 24 horas
            ),
            
            # Transiciones de rollback
            (DebtorState.PENDIENTE_PAGO, DebtorState.VERDE): StateTransition(
                from_state=DebtorState.PENDIENTE_PAGO,
                to_state=DebtorState.VERDE,
                trigger="payment_timeout",
                conditions=["payment_expired"],
                actions=["reset_payment_link", "schedule_new_contact"],
                auto_rollback=True
            ),
            
            (DebtorState.EN_NEGOCIACION, DebtorState.AMARILLO): StateTransition(
                from_state=DebtorState.EN_NEGOCIACION,
                to_state=DebtorState.AMARILLO,
                trigger="negotiation_timeout",
                conditions=["negotiation_expired"],
                actions=["reset_negotiation", "schedule_new_approach"],
                auto_rollback=True
            )
        }
        
        # Estados temporales con timeouts
        self.temporary_states = {
            DebtorState.PENDIENTE_PAGO: 2880,  # 48 horas
            DebtorState.EN_NEGOCIACION: 720,    # 12 horas
            DebtorState.ESCALADO_HUMANO: 1440,  # 24 horas
            DebtorState.EN_SEGUIMIENTO: 1440    # 24 horas
        }
        
        # Historial de cambios de estado
        self.state_history: Dict[int, List[StateHistory]] = {}
    
    def can_transition(
        self, 
        from_state: DebtorState, 
        to_state: DebtorState, 
        context: Dict[str, Any]
    ) -> bool:
        """Verifica si una transición es válida"""
        transition_key = (from_state, to_state)
        
        if transition_key not in self.transitions:
            logger.warning(f"Transición no válida: {from_state} -> {to_state}")
            return False
        
        transition = self.transitions[transition_key]
        
        # Verificar condiciones
        for condition in transition.conditions:
            if not self._evaluate_condition(condition, context):
                logger.info(f"Condición no cumplida: {condition}")
                return False
        
        return True
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evalúa una condición de transición"""
        condition_map = {
            "has_identity_confirmation": lambda ctx: ctx.get("identity_confirmed", False),
            "positive_response": lambda ctx: ctx.get("response_sentiment", "neutral") in ["positive", "very_positive"],
            "asks_for_discount": lambda ctx: ctx.get("asks_for_discount", False),
            "refuses_payment": lambda ctx: ctx.get("refuses_payment", False),
            "aggressive_behavior": lambda ctx: ctx.get("aggressive_behavior", False),
            "payment_intent": lambda ctx: ctx.get("payment_intent", False),
            "discount_accepted": lambda ctx: ctx.get("discount_accepted", False),
            "payment_link_generated": lambda ctx: ctx.get("payment_link_generated", False),
            "discount_requested": lambda ctx: ctx.get("discount_requested", False),
            "payment_plan_discussed": lambda ctx: ctx.get("payment_plan_discussed", False),
            "counter_offer_made": lambda ctx: ctx.get("counter_offer_made", False),
            "escalation_required": lambda ctx: ctx.get("escalation_required", False),
            "payment_expired": lambda ctx: ctx.get("payment_expired", False),
            "negotiation_expired": lambda ctx: ctx.get("negotiation_expired", False)
        }
        
        evaluator = condition_map.get(condition)
        if evaluator:
            return evaluator(context)
        
        logger.warning(f"Condición no reconocida: {condition}")
        return False
    
    def transition_state(
        self,
        db: Session,
        debtor_id: int,
        new_state: DebtorState,
        trigger: str,
        context: Dict[str, Any],
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Realiza una transición de estado"""
        try:
            debtor = db.query(Debtor).filter(Debtor.id == debtor_id).first()
            if debtor is None:
                logger.error(f"Deudor no encontrado: {debtor_id}")
                return False
            
            current_state = DebtorState(str(debtor.state)) if debtor.state else DebtorState.GRIS
            
            # Verificar si la transición es válida
            if not self.can_transition(current_state, new_state, context):
                logger.warning(f"Transición no válida: {current_state} -> {new_state}")
                return False
            
            # Obtener transición
            transition = self.transitions.get((current_state, new_state))
            if not transition:
                logger.error(f"Transición no definida: {current_state} -> {new_state}")
                return False
            
            # Ejecutar acciones de la transición
            for action in transition.actions:
                self._execute_action(action, debtor, context, db)
            
            # Actualizar estado
            old_state = str(debtor.state) if debtor.state else "GRIS"
            setattr(debtor, 'state', new_state.value)
            
            # Registrar cambio de estado
            self._log_state_change(debtor_id, old_state, new_state.value, trigger, user_id, notes)
            
            # Programar rollback si es necesario
            if transition.auto_rollback and transition.timeout_minutes:
                self._schedule_rollback(debtor_id, current_state, transition.timeout_minutes)
            
            db.commit()
            logger.info(f"Estado del deudor {debtor_id} cambiado: {old_state} -> {new_state.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en transición de estado: {e}")
            db.rollback()
            return False
    
    def _execute_action(self, action: str, debtor: Debtor, context: Dict[str, Any], db: Session):
        """Ejecuta una acción de transición"""
        try:
            if action == "generate_payment_link":
                # TODO: Integrar con payment_link_service
                logger.info(f"Generando link de pago para deudor {debtor.id}")
                
            elif action == "update_contact_schedule":
                # TODO: Integrar con followup_service
                logger.info(f"Actualizando agenda de contacto para deudor {debtor.id}")
                
            elif action == "offer_discount":
                # TODO: Integrar con rule_decision_service
                logger.info(f"Ofreciendo descuento a deudor {debtor.id}")
                
            elif action == "schedule_followup":
                # TODO: Integrar con followup_service
                logger.info(f"Programando seguimiento para deudor {debtor.id}")
                
            elif action == "escalate_to_human":
                # TODO: Integrar con notification_service
                logger.info(f"Escalando deudor {debtor.id} a humano")
                
            elif action == "log_negative_interaction":
                # TODO: Integrar con traceability_service
                logger.info(f"Registrando interacción negativa para deudor {debtor.id}")
                
            elif action == "apply_discount":
                # TODO: Integrar con payment_link_service
                logger.info(f"Aplicando descuento a deudor {debtor.id}")
                
            elif action == "schedule_payment_reminder":
                # TODO: Integrar con followup_service
                logger.info(f"Programando recordatorio de pago para deudor {debtor.id}")
                
            elif action == "offer_payment_plan":
                # TODO: Integrar con rule_decision_service
                logger.info(f"Ofreciendo plan de pago a deudor {debtor.id}")
                
            elif action == "schedule_negotiation_followup":
                # TODO: Integrar con followup_service
                logger.info(f"Programando seguimiento de negociación para deudor {debtor.id}")
                
            elif action == "evaluate_counter_offer":
                # TODO: Integrar con rule_decision_service
                logger.info(f"Evaluando contraoferta de deudor {debtor.id}")
                
            elif action == "schedule_response":
                # TODO: Integrar con followup_service
                logger.info(f"Programando respuesta para deudor {debtor.id}")
                
            elif action == "assign_to_human":
                # TODO: Integrar con notification_service
                logger.info(f"Asignando deudor {debtor.id} a humano")
                
            elif action == "log_escalation":
                # TODO: Integrar con traceability_service
                logger.info(f"Registrando escalación para deudor {debtor.id}")
                
            elif action == "reset_payment_link":
                # TODO: Integrar con payment_link_service
                logger.info(f"Reseteando link de pago para deudor {debtor.id}")
                
            elif action == "schedule_new_contact":
                # TODO: Integrar con followup_service
                logger.info(f"Programando nuevo contacto para deudor {debtor.id}")
                
            elif action == "reset_negotiation":
                # TODO: Integrar con rule_decision_service
                logger.info(f"Reseteando negociación para deudor {debtor.id}")
                
            elif action == "schedule_new_approach":
                # TODO: Integrar con followup_service
                logger.info(f"Programando nuevo enfoque para deudor {debtor.id}")
                
            else:
                logger.warning(f"Acción no reconocida: {action}")
                
        except Exception as e:
            logger.error(f"Error ejecutando acción {action}: {e}")
    
    def _log_state_change(
        self,
        debtor_id: int,
        from_state: str,
        to_state: str,
        trigger: str,
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ):
        """Registra un cambio de estado"""
        history_entry = StateHistory(
            timestamp=datetime.utcnow(),
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            user_id=user_id,
            notes=notes
        )
        
        if debtor_id not in self.state_history:
            self.state_history[debtor_id] = []
        
        self.state_history[debtor_id].append(history_entry)
    
    def _schedule_rollback(self, debtor_id: int, original_state: DebtorState, timeout_minutes: int):
        """Programa un rollback automático"""
        # TODO: Implementar con sistema de tareas programadas (Celery, etc.)
        logger.info(f"Programando rollback para deudor {debtor_id} en {timeout_minutes} minutos")
    
    def get_state_history(self, debtor_id: int) -> List[StateHistory]:
        """Obtiene el historial de estados de un deudor"""
        return self.state_history.get(debtor_id, [])
    
    def is_temporary_state(self, state: DebtorState) -> bool:
        """Verifica si un estado es temporal"""
        return state in self.temporary_states
    
    def get_state_timeout(self, state: DebtorState) -> Optional[int]:
        """Obtiene el timeout de un estado temporal"""
        return self.temporary_states.get(state)
    
    def get_valid_transitions(self, current_state: DebtorState) -> List[DebtorState]:
        """Obtiene las transiciones válidas desde un estado"""
        valid_transitions = []
        
        for (from_state, to_state) in self.transitions.keys():
            if from_state == current_state:
                valid_transitions.append(to_state)
        
        return valid_transitions

# Instancia global del servicio
state_machine_service = StateMachineService() 