from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class CreateOrUpdateFAQ(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None


class ReadFAQ(BaseModel):
    uid: uuid.UUID
    question: str
    answer: str
    domain: str = Field(default="https://jeremiahedavid.online")
    createdAt: datetime

    class Config:
        from_attributes = True
