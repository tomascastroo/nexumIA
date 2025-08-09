import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from fastapi import FastAPI, Request
from fastapi.responses import Response
from routers import campaign,strategy,bot,test_whatsapp,webhook,traceability
from middleware.security_middleware import setup_cors_middleware, setup_security_middleware
from apscheduler.schedulers.background import BackgroundScheduler
from services.followup_service import run_daily_followups
from db.db import SessionLocal
from routers.debt_payment import router as debt_payment_router
from core.metrics import router as metrics_router
import time
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic.json import pydantic_encoder
import json
from pydantic import TypeAdapter
from pydantic import ConfigDict
from routers.strategy import router as strategy_router
from fastapi_limiter import FastAPILimiter
import redis.asyncio as aioredis
from routers.api.v1 import auth as auth_v1
from routers.api.v1 import debtor as debtor_v1
from routers.api.v1 import debtor_dataset_router as debtor_dataset_router_v1
from routers.api.v1 import debtor_custom_field_router as debtor_custom_field_router_v1

app = FastAPI(
    title="Nexum IA - Sistema de Gestión de Cobranzas",
    description="API para gestión inteligente de deudores con IA",
    version="1.0.0"
)

setup_cors_middleware(app)
setup_security_middleware(app)

scheduler = BackgroundScheduler()

def get_db_for_scheduler():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    if os.getenv("DISABLE_RATE_LIMITER", "false").lower() == "true":
        return
    # Initialize Redis for rate limiting
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    redis_kwargs = {"encoding": "utf-8", "decode_responses": True}
    if REDIS_PASSWORD not in (None, "", "null", "None"):
        redis_kwargs["password"] = REDIS_PASSWORD
    redis = await aioredis.from_url(redis_url, **redis_kwargs)
    await FastAPILimiter.init(redis)
    scheduler.add_job(run_daily_followups, 'interval', days=1, args=[next(get_db_for_scheduler())])
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

# Middleware para logging y métricas
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log de la request
    request_id = getattr(request.state, 'request_id', 'unknown')
    user_id = getattr(request.state, 'user_id', None)
    # log_request( # This line was removed as per the edit hint
    #     request_id=request_id,
    #     method=request.method,
    #     url=str(request.url),
    #     status_code=response.status_code,
    #     user_id=user_id,
    #     duration=process_time
    # )
    
    # Agregar header de tiempo de procesamiento
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Endpoint de health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


app.include_router(auth_v1.router, prefix="/api/v1/auth")
app.include_router(debtor_dataset_router_v1.router, prefix="/api/v1")
app.include_router(debtor_custom_field_router_v1.router, prefix="/api/v1")
app.include_router(debtor_v1.router, prefix="/api/v1")
app.include_router(campaign.router, prefix="/api/v1/campaign")
app.include_router(bot.router, prefix="/api/v1/bot")
app.include_router(strategy_router, prefix="/api/v1/strategy")
app.include_router(traceability.router, prefix="/api/v1/traceability")
app.include_router(debt_payment_router, prefix="/api/v1/debt-payment")
app.include_router(test_whatsapp.router, prefix="/whatsapp")
app.include_router(webhook.router, prefix="/webhook")
app.include_router(metrics_router)

print("CORS origins permitidos:", os.getenv("ALLOWED_ORIGINS"))