from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.prompts.citation_prompt import SYSTEM_PROMPT, build_user_prompt


class OpenAIClient:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for LLM answers")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.settings.openai_embedding_model, input=texts)
        return [item.embedding for item in response.data]

    def answer(self, query: str, excerpts: list[tuple[str, str]]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(query, excerpts)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
