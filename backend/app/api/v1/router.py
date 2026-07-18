from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.charts import router as charts_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.usage import router as usage_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(charts_router)
api_router.include_router(conversations_router)
api_router.include_router(documents_router)
api_router.include_router(usage_router)
