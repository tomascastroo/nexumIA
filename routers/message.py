from fastapi import APIRouter, Body
from tasks.whatsapp_tasks import send_whatsapp_message
from tasks.celery_app import celery_app
from tasks.ia_tasks import analyze_debtors, save_conversation

router = APIRouter()

@router.post("/whatsapp/send")
async def send_whatsapp(payload: dict = Body(...)):
    task = send_whatsapp_message.delay(payload)
    return {"task_id": task.id, "status": "processing"}

@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }

# Endpoints mínimos para pruebas de Celery IA (solo en test/QA)
@router.post("/debtors/analyze")
async def analyze_debtors_endpoint(payload: list = Body(...)):
    task = analyze_debtors.delay(payload)
    return {"task_id": task.id, "status": "processing"}

@router.post("/debtors/conversation")
async def save_conversation_endpoint(payload: dict = Body(...)):
    task = save_conversation.delay(payload)
    return {"task_id": task.id, "status": "processing"}
