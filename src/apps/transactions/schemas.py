from pydantic import BaseModel, Field, constr, conint, condecimal, UUID4
from typing import Annotated, Optional, List
from datetime import datetime
import uuid
from decimal import Decimal
from .enums import (
    TransactionStatus,
    TransactionPaymentType,
    TransactionPaymentMethod
)


# Pydantic model for PlanFeatures
class PlanFeatureLinksRead(BaseModel):
    featureUid: Optional[uuid.UUID]
    planUid: Optional[uuid.UUID]


class CreateOrUpdatePlanFeatures(BaseModel):
    name: Annotated[str, constr(min_length=1, max_length=255)]  # constr for name validation
    featured: bool = Field(default=False)


class PlanFeaturesRead(BaseModel):
    uid: UUID4 = Field(default_factory=uuid.uuid4)
    name: Annotated[str, constr(min_length=1, max_length=255)]  # constr for name validation
    featured: bool = Field(default=False)
    plans: List[PlanFeatureLinksRead] = []

    class Config:
        from_attributes = True


# Pydantic model for Plans
class PlansCreateOrUpdate(BaseModel):
    name: Annotated[str, constr(min_length=1, max_length=255)]  # constr for name validation
    description: Annotated[str, constr(min_length=1, max_length=500)]  # constr for description validation
    trialInDays: Annotated[int, conint(gt=0)] = Field(default=60)  # conint to ensure trialInDays is a positive integer
    amount: Annotated[Decimal, condecimal(max_digits=20, decimal_places=2)] = Field(default=Decimal('0.00'))  # condecimal for amount validation
    duration: Annotated[int, conint(gt=0)]  # conint to ensure duration is a positive integer (in months)


class PlansRead(BaseModel):
    uid: UUID4 = Field(default_factory=uuid.uuid4)
    name: Annotated[str, constr(min_length=1, max_length=255)]  # constr for name validation
    description: Annotated[str, constr(min_length=1, max_length=500)]  # constr for description validation
    features: List[PlanFeatureLinksRead] = []
    subscriptions: List["SubscriptionRead"]
    trialInDays: Annotated[int, conint(gt=0)] = Field(default=60)  # conint to ensure trialInDays is a positive integer
    amount: Annotated[Decimal, condecimal(max_digits=20, decimal_places=2)] = Field(default=Decimal('0.00'))  # condecimal for amount validation
    duration: Annotated[int, conint(gt=0)]  # conint to ensure duration is a positive integer (in months)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# Pydantic model for Subscription
class CreateOrUpdateSubscription(BaseModel):
    uid: UUID4 = Field(default_factory=uuid.uuid4)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)  # assuming TransactionStatus is an enum, can be str


class SubscriptionRead(BaseModel):
    uid: UUID4 = Field(default_factory=uuid.uuid4)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)  # assuming TransactionStatus is an enum, can be str
    planUid: Optional[UUID4]
    paidDate: datetime = Field(default_factory=datetime.utcnow)
    expiryDate: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True


# Pydantic model for transactions
class TransactionHistoryCreateOrUpdate(BaseModel):
    amountPaid: Annotated[Decimal, Optional[condecimal(max_digits=10, decimal_places=2)]]  # Optional update for amount paid
    status: Optional[TransactionStatus]  # Can replace with TransactionStatus Enum type
    transactionType: Optional[TransactionPaymentType]  # Optional update
    method: Optional[TransactionPaymentMethod]  # Optional update for payment method


# Pydantic schema for reading a TransactionHistory (full object)
class TransactionHistoryRead(BaseModel):
    uid: UUID4
    transactionId: str
    amountPaid: Annotated[Decimal, Optional[condecimal(max_digits=10, decimal_places=2)]]  # Optional update for amount paid
    status: Optional[TransactionStatus]  # Can replace with TransactionStatus Enum type
    transactionType: Optional[TransactionPaymentType]  # Optional update
    method: Optional[TransactionPaymentMethod]  # Optional update for payment method
    payerUid: Optional[UUID4]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True

