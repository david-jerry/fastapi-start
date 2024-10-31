from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import UploadFile
from pydantic import BaseModel, IPvAnyAddress


class CreateOrUpdateFAQ(BaseModel):
    question: Optional[str]
    answer: Optional[str]


class ReadFAQ(BaseModel):
    uid: uuid.UUID
    question: str
    answer: str
    domainUid: uuid.UUID
    createdAt: datetime

    class Config:
        from_attributes = True


class ReadTestimonial(BaseModel):
    uid: uuid.UUID
    name: str
    work: str
    company: str
    image: str
    testimony: str
    rating: int
    domainUid: uuid.UUID
    createdAt: datetime

    class Config:
        from_attributes = True


class CreateOrUpdateTestimonial(BaseModel):
    name: Optional[str]
    work: Optional[str]
    company: Optional[str]
    image: Optional[UploadFile]
    testimony: Optional[str]
    rating: Optional[int]


class CreateOrUpdateAnalytics(BaseModel):
    pathname: str


class AnalyticsRead(BaseModel):
    uid: uuid.UUID
    pathname: str
    pageViews: List["PageViewRead"]
    domainUid: uuid.UUID
    createdAt: datetime


class PageViewRead(BaseModel):
    uid: uuid.UUID
    ip: IPvAnyAddress
    buttonsClicked: List[str]
    timeSpendInSeconds: int
    date: datetime
    analyticsUid: uuid.UUID

class CreateOrUpdatePageView(BaseModel):
    ip: Optional[IPvAnyAddress]
    buttonsClicked: Optional[List[str]]
    timeSpendInSeconds: Optional[int]
