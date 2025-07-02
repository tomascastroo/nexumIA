from fastapi import FastAPI
from routers import campaign,debtor,strategy,bot,test_whatsapp,webhook,auth
from middleware.cors import setup_cors

app = FastAPI()
setup_cors(app)

app.include_router(campaign.router,prefix="/campaign")
app.include_router(bot.router,prefix="/bot")
app.include_router(strategy.router,prefix="/strategy")
app.include_router(debtor.router,prefix="/debtor")
app.include_router(test_whatsapp.router,prefix="/whatsapp")
app.include_router(webhook.router,prefix="/webhook")
app.include_router(auth.router,prefix="/auth")

