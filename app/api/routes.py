from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Union

from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import APIError, AuthenticationError, RateLimitError
from pydantic import BaseModel

from app.models.response_model import QueryResponse
from app.services.query_service import QueryService


class QueryRequest(BaseModel):
    query: str
    limit: int = 5


def create_router(service: QueryService) -> APIRouter:
    router = APIRouter()

    def openai_http_error(error: APIError) -> HTTPException:
        if isinstance(error, RateLimitError):
            return HTTPException(status_code=503, detail="OpenAI quota is unavailable. Add credits or use an API key with available quota.")
        if isinstance(error, AuthenticationError):
            return HTTPException(status_code=503, detail="OpenAI rejected the API key. Replace OPENAI_API_KEY in .env and restart the backend.")
        return HTTPException(status_code=502, detail="OpenAI could not process the request. Check the backend logs for details.")

    @router.post("/documents")
    async def upload_document(file: UploadFile = File(...)) -> dict[str, Union[int, str]]:
        if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Upload a PDF file")
        content = await file.read()
        with NamedTemporaryFile(suffix=".pdf", delete=False) as temporary:
            temporary.write(content)
            temporary_path = temporary.name
        try:
            try:
                count = service.ingest(temporary_path)
            except APIError as error:
                raise openai_http_error(error) from error
        finally:
            Path(temporary_path).unlink(missing_ok=True)
        return {"filename": file.filename, "chunks": count}

    @router.post("/query", response_model=QueryResponse)
    async def query_document(request: QueryRequest) -> QueryResponse:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        if not service.chunks:
            raise HTTPException(status_code=400, detail="Upload a document first")
        if service.llm_client is None:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured. Add it to .env and restart the backend.")
        try:
            return service.query(request.query, request.limit)
        except APIError as error:
            raise openai_http_error(error) from error

    return router
