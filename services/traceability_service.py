from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from services.rule_decision_service import RuleDecision
import structlog

logger = structlog.get_logger()

class TraceabilityService:
    """Servicio para registrar y consultar trazabilidad de decisiones de reglas"""
    
    def __init__(self):
        self.decision_logs: List[Dict[str, Any]] = []
    
    def log_rule_decision(
        self,
        debtor_id: int,
        strategy_id: int,
        user_message: str,
        decision: RuleDecision,
        llm_response: str,
        conversation_history: List[Dict[str, str]],
        debtor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra una decisión de reglas con toda la información de trazabilidad.
        
        Args:
            debtor_id: ID del deudor
            strategy_id: ID de la estrategia
            user_message: Mensaje del usuario
            decision: Decisión tomada por las reglas
            llm_response: Respuesta generada por el LLM
            conversation_history: Historial de conversación
            debtor_data: Datos del deudor
            
        Returns:
            Log de la decisión registrada
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'debtor_id': debtor_id,
            'strategy_id': strategy_id,
            'user_message': user_message,
            'llm_response': llm_response,
            'decision': {
                'action_type': decision.action_type,
                'action_description': decision.action_description,
                'triggered_rule': decision.triggered_rule,
                'applicable_rules': decision.applicable_rules,
                'restrictions': decision.restrictions,
                'allowed_responses': decision.allowed_responses,
                'reasoning': decision.reasoning,
                'fallback_reason': decision.fallback_reason
            },
            'context': {
                'debtor_data': debtor_data,
                'conversation_length': len(conversation_history),
                'last_messages': conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            },
            'metadata': {
                'total_rules_evaluated': len(decision.applicable_rules),
                'has_strict_rules': any(rule.get('strict', False) for rule in decision.applicable_rules),
                'has_fallback': decision.action_type == 'fallback'
            }
        }
        
        self.decision_logs.append(log_entry)
        
        # Imprimir para debugging
        self._print_decision_summary(log_entry)
        
        return log_entry
    
    def _print_decision_summary(self, log_entry: Dict[str, Any]):
        """Imprime un resumen de la decisión para debugging"""
        decision = log_entry['decision']
        
        logger.debug(f"🎯 DECISIÓN DE REGLAS - {log_entry['timestamp']}")
        logger.debug(f"📱 Deudor ID: {log_entry['debtor_id']}")
        logger.debug(f"📋 Estrategia ID: {log_entry['strategy_id']}")
        logger.debug(f"💬 Mensaje usuario: {log_entry['user_message'][:100]}...")
        logger.debug(f"🤖 Acción decidida: {decision['action_description']}")
        logger.debug(f"📊 Reglas aplicables: {len(decision['applicable_rules'])}")
        
        if decision['triggered_rule']:
            rule = decision['triggered_rule']
            logger.debug(f"🎯 Regla activada: {rule.get('name', 'Sin nombre')}")
            logger.debug(f"📊   Tipo: {rule.get('rule_type', 'Desconocido')}")
            logger.debug(f"📊   Prioridad: {rule.get('priority', 1)}")
            logger.debug(f"📊   Estricta: {rule.get('strict', False)}")
        
        logger.debug(f"🔒 Restricciones: {len(decision['restrictions'] or [])}")
        logger.debug(f"✅ Respuestas permitidas: {len(decision['allowed_responses'] or [])}")
        logger.debug(f"🧠 Razonamiento: {decision['reasoning']}")
        
        if decision['fallback_reason']:
            logger.debug(f"⚠️  Fallback: {decision['fallback_reason']}")
        
        logger.debug(f"🤖 Respuesta LLM: {log_entry['llm_response'][:100]}...")
    
    def get_decision_history(
        self,
        debtor_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de decisiones con filtros opcionales.
        
        Args:
            debtor_id: Filtrar por deudor específico
            strategy_id: Filtrar por estrategia específica
            limit: Límite de resultados
            
        Returns:
            Lista de decisiones filtradas
        """
        filtered_logs = self.decision_logs
        
        if debtor_id is not None:
            filtered_logs = [log for log in filtered_logs if log['debtor_id'] == debtor_id]
        
        if strategy_id is not None:
            filtered_logs = [log for log in filtered_logs if log['strategy_id'] == strategy_id]
        
        # Ordenar por timestamp descendente
        filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered_logs[:limit]
    
    def get_decision_analytics(
        self,
        debtor_id: Optional[int] = None,
        strategy_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera analytics de las decisiones tomadas.
        
        Args:
            debtor_id: Filtrar por deudor específico
            strategy_id: Filtrar por estrategia específica
            
        Returns:
            Analytics de decisiones
        """
        logs = self.get_decision_history(debtor_id, strategy_id)
        
        if not logs:
            return {
                'total_decisions': 0,
                'action_types': {},
                'fallback_rate': 0.0,
                'strict_rules_usage': 0.0,
                'average_rules_per_decision': 0.0
            }
        
        # Contar tipos de acción
        action_types = {}
        fallback_count = 0
        strict_rules_count = 0
        total_rules = 0
        
        for log in logs:
            action_type = log['decision']['action_type']
            action_types[action_type] = action_types.get(action_type, 0) + 1
            
            if action_type == 'fallback':
                fallback_count += 1
            
            if log['metadata']['has_strict_rules']:
                strict_rules_count += 1
            
            total_rules += log['metadata']['total_rules_evaluated']
        
        total_decisions = len(logs)
        
        return {
            'total_decisions': total_decisions,
            'action_types': action_types,
            'fallback_rate': (fallback_count / total_decisions) * 100 if total_decisions > 0 else 0,
            'strict_rules_usage': (strict_rules_count / total_decisions) * 100 if total_decisions > 0 else 0,
            'average_rules_per_decision': total_rules / total_decisions if total_decisions > 0 else 0,
            'recent_decisions': logs[:10]  # Últimas 10 decisiones
        }
    
    def export_decision_logs(
        self,
        debtor_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        format: str = 'json'
    ) -> str:
        """
        Exporta los logs de decisiones en diferentes formatos.
        
        Args:
            debtor_id: Filtrar por deudor específico
            strategy_id: Filtrar por estrategia específica
            format: Formato de exportación ('json', 'csv')
            
        Returns:
            Datos exportados en el formato especificado
        """
        logs = self.get_decision_history(debtor_id, strategy_id)
        
        if format == 'json':
            return json.dumps(logs, indent=2, ensure_ascii=False)
        elif format == 'csv':
            # Implementar exportación CSV si es necesario
            return "CSV export not implemented yet"
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def clear_logs(self):
        """Limpia todos los logs (solo para testing)"""
        self.decision_logs.clear()

# Instancia global del servicio
traceability_service = TraceabilityService() 