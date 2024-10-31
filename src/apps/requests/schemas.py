from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import UploadFile
from pydantic import BaseModel, EmailStr, Field, IPvAnyAddress
from pydantic_extra_types.phone_numbers import PhoneNumber


class CreateOrUpdateService(BaseModel):
    name: Optional[str]
    description: Optional[str]
    minDuration: Optional[int]
    maxDuration: Optional[int]


class ServicesRead(BaseModel):
    uid: uuid.UUID
    name: Optional[str]
    domain: Optional[str]
    description: Optional[str]
    minDuration: Optional[int]
    maxDuration: Optional[int]

    features: List["ServiceFeaturesRead"]

    createdAt: datetime

    class Config:
        from_attributes = True


class CreateOrUpdateServiceFeatures(BaseModel):
    name: Optional[str]
    description: Optional[str]
    image: Optional[UploadFile] = None
    minPrice: Optional[Decimal] = None
    maxPrice: Optional[Decimal] = None


class ServiceFeaturesRead(BaseModel):
    uid: uuid.UUID
    name: Optional[str]
    image: Optional[str] = Field(default="https://placeholder.co/400")
    description: Optional[str]
    minPrice: Decimal = Field(default=0.00)
    maxPrice: Decimal = Field(default=0.00)

    serviceUid: Optional[uuid.UUID]

    createdAt: datetime

    class Config:
        from_attributes = True


class CreateRequestedServices(BaseModel):
    clientName: str
    clientEmail: EmailStr
    clientPhone: Optional[PhoneNumber]
    description: str
    services: List[uuid.UUID] # List of service features uid under a specific service


class UpdateRequestedServices(BaseModel):
    initialDeposit: Optional[Decimal] = None
    reviewDeposit: Optional[Decimal] = None
    finalDeposit: Optional[Decimal] = None
    rating: Optional[int] = None
    expectedDeliveryDate: Optional[date] = None
    deliveredDate: Optional[date] = None


class RequestedServicesRead(BaseModel):
    uid: uuid.UUID
    clientName: str
    clientEmail: EmailStr
    clientPhone: Optional[PhoneNumber]
    description: str
    domain: str
    totalCost: Decimal = Field(default=0.00, decimal_places=2)
    initialDeposit: Decimal = Field(default=0.00, decimal_places=2)
    reviewDeposit: Decimal = Field(default=0.00, decimal_places=2)
    finalDeposit: Decimal = Field(default=0.00, decimal_places=2)
    rating: int = Field(default=5)
    expectedDeliveryDate: Optional[date] = None
    deliveredDate: Optional[date] = None

    services: List[ServiceFeaturesRead]
    milestones: List["MilestonesRead"]

    createdAt: datetime

    class Config:
        from_attributes = True


class CreateOrUpdateMilestones(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    expectedDeliveryDate: Optional[date] = None
    completed: Optional[bool] = None


class MilestonesRead(BaseModel):
    uid: uuid.UUID
    name: str
    description: str
    duration: int
    expectedDeliveryDate: date
    completed: bool
    createdAt: datetime
