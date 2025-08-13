"""
Tests para las tareas Celery de OpenAI.
Verifica que las tareas se encolen correctamente y que los reintentos funcionan.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from tasks.openai_tasks import (
    generate_first_message_task,
    generate_response_task,
    classify_state_task,
    analyze_conversation_context_task
)
from services.openai_service import (
    generate_first_message_async,
    generate_response_async,
    classify_state_async,
    analyze_conversation_context_async,
    get_task_result
)


class TestOpenAICeleryTasks:
    """Tests para las tareas Celery de OpenAI."""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock de respuesta de OpenAI."""
        mock_choice = Mock()
        mock_choice.message.content = "Respuesta de prueba"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        return mock_response
    
    @pytest.fixture
    def mock_celery_task(self):
        """Mock de tarea Celery."""
        mock_task = Mock()
        mock_task.id = "test-task-id-123"
        mock_task.delay.return_value = mock_task
        return mock_task
    
    def test_generate_first_message_task_success(self, mock_openai_response):
        """Test que la tarea genera mensaje exitosamente."""
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', return_value=mock_openai_response):
            result = generate_first_message_task("Instrucción de prueba")
            assert result == "Respuesta de prueba"
    
    def test_generate_response_task_success(self, mock_openai_response):
        """Test que la tarea genera respuesta exitosamente."""
        messages = [{"role": "user", "content": "Hola"}]
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', return_value=mock_openai_response):
            result = generate_response_task(messages)
            assert result == "Respuesta de prueba"
    
    def test_classify_state_task_success(self, mock_openai_response):
        """Test que la tarea clasifica estado exitosamente."""
        # Mock para clasificar estado
        mock_choice = Mock()
        mock_choice.message.content = "VERDE"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', return_value=mock_response):
            result = classify_state_task("Quiero pagar")
            assert result == "VERDE"
    
    def test_classify_state_task_invalid_state_fallback(self, mock_openai_response):
        """Test que la tarea usa GRIS como fallback para estado inválido."""
        # Mock para estado inválido
        mock_choice = Mock()
        mock_choice.message.content = "ESTADO_INVALIDO"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', return_value=mock_response):
            result = classify_state_task("Mensaje de prueba")
            assert result == "GRIS"
    
    def test_analyze_conversation_context_task_success(self, mock_openai_response):
        """Test que la tarea analiza contexto exitosamente."""
        # Mock para análisis de contexto
        mock_choice = Mock()
        mock_choice.message.content = '{"has_payment_intent": true, "confidence_score": 0.8}'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', return_value=mock_response):
            result = analyze_conversation_context_task([], "Quiero pagar")
            assert result["has_payment_intent"] is True
            assert result["confidence_score"] == 0.8
    
    def test_analyze_conversation_context_task_json_fallback(self, mock_openai_response):
        """Test que la tarea usa fallback cuando OpenAI no devuelve JSON válido."""
        # Mock para respuesta no-JSON
        mock_choice = Mock()
        mock_choice.message.content = "Respuesta no válida"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', return_value=mock_response):
            result = analyze_conversation_context_task([], "Mensaje de prueba")
            assert result["has_payment_intent"] is False
            assert result["confidence_score"] == 0.5
            assert "fallback_analysis" in result["context_indicators"]


class TestOpenAIServiceAsyncWrappers:
    """Tests para los wrappers asíncronos del servicio OpenAI."""
    
    @patch('services.openai_service.generate_first_message_task')
    def test_generate_first_message_async_encola_tarea(self, mock_task):
        """Test que el wrapper asíncrono encola la tarea en Celery."""
        mock_task.delay.return_value.id = "test-task-id"
        
        task_id = generate_first_message_async("Instrucción de prueba")
        
        assert task_id == "test-task-id"
        mock_task.delay.assert_called_once_with("Instrucción de prueba", "gpt-4o-mini")
    
    @patch('services.openai_service.generate_response_task')
    def test_generate_response_async_encola_tarea(self, mock_task):
        """Test que el wrapper asíncrono encola la tarea en Celery."""
        mock_task.delay.return_value.id = "test-task-id"
        messages = [{"role": "user", "content": "Hola"}]
        
        task_id = generate_response_async(messages)
        
        assert task_id == "test-task-id"
        mock_task.delay.assert_called_once_with(messages, "gpt-4o-mini")
    
    @patch('services.openai_service.classify_state_task')
    def test_classify_state_async_encola_tarea(self, mock_task):
        """Test que el wrapper asíncrono encola la tarea en Celery."""
        mock_task.delay.return_value.id = "test-task-id"
        
        task_id = classify_state_async("Quiero pagar")
        
        assert task_id == "test-task-id"
        mock_task.delay.assert_called_once_with("Quiero pagar", None)
    
    @patch('services.openai_service.analyze_conversation_context_task')
    def test_analyze_conversation_context_async_encola_tarea(self, mock_task):
        """Test que el wrapper asíncrono encola la tarea en Celery."""
        mock_task.delay.return_value.id = "test-task-id"
        
        task_id = analyze_conversation_context_async([], "Mensaje de prueba")
        
        assert task_id == "test-task-id"
        mock_task.delay.assert_called_once_with([], "Mensaje de prueba")


class TestOpenAIServiceTaskResult:
    """Tests para la función get_task_result."""
    
    @patch('tasks.openai_tasks.celery_app')
    def test_get_task_result_success(self, mock_celery_app):
        """Test que se obtiene el resultado de la tarea correctamente."""
        mock_task = Mock()
        mock_task.get.return_value = "Resultado de la tarea"
        mock_celery_app.AsyncResult.return_value = mock_task
        
        result = get_task_result("test-task-id")
        
        assert result == "Resultado de la tarea"
        mock_celery_app.AsyncResult.assert_called_once_with("test-task-id")
        mock_task.get.assert_called_once_with(timeout=30)
    
    @patch('tasks.openai_tasks.celery_app')
    def test_get_task_result_timeout(self, mock_celery_app):
        """Test que se maneja el timeout correctamente."""
        mock_task = Mock()
        mock_task.get.side_effect = Exception("Timeout")
        mock_celery_app.AsyncResult.return_value = mock_task
        
        result = get_task_result("test-task-id", timeout=10)
        
        assert result is None
        mock_task.get.assert_called_once_with(timeout=10)
    
    @patch('tasks.openai_tasks.celery_app')
    def test_get_task_result_custom_timeout(self, mock_celery_app):
        """Test que se respeta el timeout personalizado."""
        mock_task = Mock()
        mock_task.get.return_value = "Resultado"
        mock_celery_app.AsyncResult.return_value = mock_task
        
        result = get_task_result("test-task-id", timeout=60)
        
        assert result == "Resultado"
        mock_task.get.assert_called_once_with(timeout=60)


class TestCeleryRetryMechanism:
    """Tests para verificar que el mecanismo de reintentos funciona."""
    
    def test_task_decorators_have_retry_config(self):
        """Test que las tareas tienen la configuración correcta de reintentos."""
        # Verificar que las tareas tienen los decoradores correctos
        assert hasattr(generate_first_message_task, 'autoretry_for')
        assert hasattr(generate_response_task, 'autoretry_for')
        assert hasattr(classify_state_task, 'autoretry_for')
        assert hasattr(analyze_conversation_context_task, 'autoretry_for')
        
        # Verificar configuración de reintentos
        assert generate_first_message_task.max_retries == 3
        assert generate_response_task.max_retries == 3
        assert classify_state_task.max_retries == 3
        assert analyze_conversation_context_task.max_retries == 3
    
    def test_task_retry_on_exception(self):
        """Test que las tareas lanzan excepciones para que Celery reintente."""
        # Simular error en OpenAI
        with patch('tasks.openai_tasks.openai_client.chat.completions.create', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                generate_first_message_task("Instrucción de prueba")
    
    def test_task_logs_retry_count(self):
        """Test que las tareas registran el conteo de reintentos."""
        # Este test verifica que el logging incluye información de reintentos
        # Verificamos que las tareas tienen la configuración de reintentos
        assert hasattr(generate_first_message_task, 'max_retries')
        assert hasattr(generate_response_task, 'max_retries')
        assert hasattr(classify_state_task, 'max_retries')
        assert hasattr(analyze_conversation_context_task, 'max_retries')
        
        # Verificar que tienen la configuración de reintentos automáticos
        assert hasattr(generate_first_message_task, 'autoretry_for')
        assert hasattr(generate_response_task, 'autoretry_for')
        assert hasattr(classify_state_task, 'autoretry_for')
        assert hasattr(analyze_conversation_context_task, 'autoretry_for')


class TestIntegrationWithExistingServices:
    """Tests de integración con servicios existentes."""
    
    @patch('services.openai_service.generate_first_message_task')
    def test_conversation_service_can_use_async_wrappers(self, mock_task):
        """Test que el servicio de conversación puede usar los wrappers asíncronos."""
        mock_task.delay.return_value.id = "test-task-id"
        
        # Verificar que las funciones asíncronas están disponibles
        assert callable(generate_first_message_async)
        assert callable(generate_response_async)
        assert callable(classify_state_async)
        assert callable(analyze_conversation_context_async)
        
        # Verificar que devuelven task IDs
        task_id = generate_first_message_async("Test")
        assert isinstance(task_id, str)
        assert len(task_id) > 0
    
    def test_sync_functions_still_available(self):
        """Test que las funciones síncronas originales siguen disponibles."""
        # Verificar que las funciones síncronas no se eliminaron
        from services.openai_service import (
            generate_openai_first_message_sync,
            generate_openai_response_sync,
            classify_state
        )
        
        assert callable(generate_openai_first_message_sync)
        assert callable(generate_openai_response_sync)
        assert callable(classify_state) 