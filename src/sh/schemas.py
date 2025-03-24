from pydantic import BaseModel, HttpUrl, validator
from typing import Optional
from datetime import datetime

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str]
    expires_at: Optional[datetime]
    
    @validator("original_url")
    def remove_trailing_slash(cls, v):
        return str(v).rstrip("/")

class LinkUpdate(BaseModel):
    original_url: HttpUrl

class LinkStats(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    last_used_at: Optional[datetime]
    clicks: int
    expires_at: Optional[datetime]
    is_deleted: Optional[bool]  

    class Config:
        orm_mode = True

class LinkSearchRequest(BaseModel):
    original_url: str

    @validator("original_url")
    def normalize_url(cls, value: str) -> str:
        return value.strip().rstrip("/")

    
class LinkSearchResponse(BaseModel):
    short_code: str
    original_url: HttpUrl
    clicks: int
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True