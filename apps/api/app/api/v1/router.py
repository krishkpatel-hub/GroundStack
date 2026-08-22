from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.discord import router as discord_router
from app.api.v1.documents import router as documents_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.ingestions import router as ingestions_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.system import router as system_router
from app.api.v1.training import router as training_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(conversations_router)
api_router.include_router(documents_router)
api_router.include_router(discord_router)
api_router.include_router(evaluation_router)
api_router.include_router(feedback_router)
api_router.include_router(ingestions_router)
api_router.include_router(metrics_router)
api_router.include_router(retrieval_router)
api_router.include_router(system_router)
api_router.include_router(training_router)
