from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import AnyHttpUrl, EmailStr, FileUrl, IPvAnyAddress
from pydantic_extra_types.phone_numbers import PhoneNumber

from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
import uuid


class ServiceRequestLink(SQLModel, table=True):
    serviceFeatureUid: uuid.UUID | None = Field(default=None, foreign_key="service_feature.uid", primary_key=True)
    requestUid: uuid.UUID | None = Field(default=None, foreign_key="requested_services.uid", primary_key=True)


class Services(SQLModel, table=True):
    __tablename__ = "services"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str = Field(unique=True)
    description: str
    domain: str
    minDuration: int = Field(default=14)
    maxDuration: int = Field(default=90)

    features: List["ServiceFeatures"] = Relationship(back_populates="service")

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    def __repr__(self) -> str:
        return f"<Services {self.name}>"


class ServiceFeatures(SQLModel, table=True):
    __tablename__ = "service_feature"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str = Field(unique=True)
    description: str
    image: Optional[str]
    minPrice: Decimal = Field(default=0.00, decimal_places=2)
    maxPrice: Decimal = Field(default=0.00, decimal_places=2)

    serviceUid: Optional[uuid.UUID] = Field(default=None, foreign_key="services.uid")
    service: Optional[Services] = Relationship(back_populates="features")

    requests: List["RequestedServices"] = Relationship(back_populates="services", link_model=ServiceRequestLink)

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    def __repr__(self) -> str:
        return f"<ServicesFeature {self.name}>"


class RequestedServices(SQLModel, table=True):
    __tablename__ = "requested_services"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    clientName: str = Field(nullable=True, default=None)
    clientEmail: EmailStr
    clientPhone: PhoneNumber = Field(nullable=True, max_length=16)

    description: str
    domain: str

    totalCost: Decimal = Field(default=0.00, decimal_places=2)
    initialDeposit: Decimal = Field(default=0.00, decimal_places=2)
    reviewDeposit: Decimal = Field(default=0.00, decimal_places=2)
    finalDeposit: Decimal = Field(default=0.00, decimal_places=2)

    services: List[ServiceFeatures] = Relationship(back_populates="requests", link_model=ServiceRequestLink)
    rating: Optional[int] = Field(default=5)

    expectedDeliveryDate: Optional[date] = Field(
        default_factory=date.today,
        sa_column=Column(pg.DATE, default=date.today),
    )
    deliveredDate: Optional[date] = Field(
        default=None,
        sa_column=Column(pg.DATE, default=date.today),
    )

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    milestones: List["Milestones"] = Relationship(
        back_populates="request",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )

    agreementTermsPdf: Optional[str] = Field(default=None)
    ndaPdf: Optional[str] = Field(default=None)

    def __repr__(self) -> str:
        return f"<RequestedServices {self.companyName}>"


class Milestones(SQLModel, table=True):
    __tablename__ = "milestones"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str = Field(default="Phase 1")
    description: str
    duration: int = Field(default=14)

    expectedDeliveryDate: Optional[date] = Field(
        default=None,
        sa_column=Column(pg.DATE, default=date.today),
    )

    requestUid: Optional[uuid.UUID] = Field(default=None, foreign_key="requested_services.uid")
    request: Optional[RequestedServices] = Relationship(back_populates="milestones")

    completed: bool = Field(default=False)

    def __repr__(self) -> str:
        return f"<MileStones {self.name}>"
