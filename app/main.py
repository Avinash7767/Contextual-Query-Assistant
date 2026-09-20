from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import create_router
from app.config import get_settings
from app.llm.openai_client import OpenAIClient
from app.services.query_service import QueryService


def create_app() -> FastAPI:
    settings = get_settings()
    client = OpenAIClient(settings) if settings.openai_api_key else None
    service = QueryService(settings, client)
    application = FastAPI(title="Contextual Query Assistant", version="1.0.0")
    application.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    application.include_router(create_router(service), prefix="/api")

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/config-status")
    async def config_status() -> dict[str, bool]:
        return {"openai_configured": bool(settings.openai_api_key)}

    return application


app = create_app()
