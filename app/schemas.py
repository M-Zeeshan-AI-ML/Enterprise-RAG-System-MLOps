from typing import List
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)

class Source(BaseModel):
    document: str
    page: int
    chunk_id: int
    content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    retrieval_count: int
