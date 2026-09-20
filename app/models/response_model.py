from pydantic import BaseModel, Field


class KeyInformation(BaseModel):
    field: str
    value: str
    citation: str


class Citation(BaseModel):
    claim: str
    location: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    summary: str
    key_information: list[KeyInformation] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: str
