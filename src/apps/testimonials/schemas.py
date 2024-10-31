from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import UploadFile
from pydantic import BaseModel, Field, IPvAnyAddress


class ReadTestimonial(BaseModel):
    uid: uuid.UUID
    name: str
    work: str
    company: Optional[str] = None
    image: Optional[str] = None
    domain: str = Field(default="https://jeremiahedavid.online")
    testimony: str
    rating: int
    createdAt: datetime

    class Config:
        from_attributes = True


class CreateOrUpdateTestimonial(BaseModel):
    name: Optional[str] = None
    work: Optional[str] = None
    company: Optional[str] = None
    testimony: Optional[str] = None
    image: Optional[UploadFile] = None
    rating: Optional[int] = None
