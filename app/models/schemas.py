from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserSignup(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshToken(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime

class Article(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[datetime] = None
    source_name: Optional[str] = None
    category: List[str] = []
    relevance_score: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    llm_summary: Optional[str] = None

class NewsResponse(BaseModel):
    articles: List[Article]
    total: int
    page: Optional[int] = 1
    page_size: Optional[int] = None
    query_info: Optional[dict] = None

class EntityExtractionResponse(BaseModel):
    entities: List[str]
    intent: str
    search_terms: List[str]
    location_hint: Optional[str] = None
