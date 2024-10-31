from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import UploadFile
from pydantic import BaseModel, Field, IPvAnyAddress


class CreateOrUpdateAnalytics(BaseModel):
    pathname: str


class AnalyticsRead(BaseModel):
    uid: uuid.UUID
    pathname: str
    domain: str = Field(default="https://jeremiahedavid.online")
    pageViews: List["PageViewRead"]
    createdAt: datetime


class PageViewRead(BaseModel):
    uid: uuid.UUID
    ip: IPvAnyAddress
    buttonsClicked: List["ButtonClickedRead"]
    timeSpendInSeconds: int = 0
    date: datetime
    analyticsUid: uuid.UUID


class CreateOrUpdatePageView(BaseModel):
    ip: Optional[IPvAnyAddress]
    buttonsClicked: str
    timeSpendInSeconds: Optional[int]


class ButtonClickedRead(BaseModel):
    uid: uuid.UUID
    buttonName: str
    pageViewUid: uuid.UUID
