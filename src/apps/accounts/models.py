from datetime import date, datetime
from decimal import Decimal
from pydantic import AnyHttpUrl, EmailStr, FileUrl, IPvAnyAddress
from pydantic_extra_types.payment import PaymentCardBrand, PaymentCardNumber
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from typing import List, Optional
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic_extra_types.country import CountryInfo

from src.apps.accounts.enums import UserGender, UserMaritalStatus
from src.apps.portfolios.models import Portfolio

# User Specific Models
class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )
    firstName: Optional[str] = Field(nullable=True, default=None)
    lastName: Optional[str] = Field(nullable=True, default=None)
    companyName: Optional[str] = Field(nullable=True, unique=True, default=None)
    phoneNumber: Optional[str] = Field(nullable=True, max_length=16, unique=True)
    email: EmailStr = Field(nullable=False, unique=True, index=True, max_length=255)
    dob: Optional[date] = Field(
        default_factory=None,
        sa_column=Column(pg.DATE, nullable=True, default=None),
    )
    image: Optional[str] = Field(nullable=True)
    passwordHash: str = Field(nullable=False)  # Store hashed passwords
    country: Optional[str] = Field(nullable=True)
    countryCode: Optional[str] = Field(nullable=True)
    countryCallingCode: Optional[str] = Field(nullable=True)
    currency: Optional[str] = Field(nullable=True)
    inEu: Optional[bool] = Field(default=False, nullable=True)

    gender: Optional[UserGender] = Field(default=UserGender.MAN)
    maritalStatus: Optional[UserMaritalStatus] = Field(default=UserMaritalStatus.SINGLE)

    # Permissions
    isBlocked: bool = Field(default=False)
    isCompany: bool = Field(default=False)
    isSuperuser: bool = Field(default=False)

    # Dates
    joined: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )
    updatedAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )

    # Relationships
    knownIps: List["KnownIps"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    bannedIps: List["BannedIps"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    verifiedEmails: List["VerifiedEmail"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    cards: List["Card"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    portfolios: List["Portfolio"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )

    @property
    def age(self) -> Optional[int]:
        if self.dob:
            today = datetime.today().date()
            age = today.year - self.dob.year - (
                (today.month, today.day) < (self.dob.month, self.dob.day)
            )
            return age
        return 0

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class KnownIps(SQLModel, table=True):
    __tablename__ = "known_ips"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )
    ip: str

    # Foreign Key to User
    userUid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional[User] = Relationship(back_populates="knownIps")

    def __repr__(self) -> str:
        return f"<KnownIp {self.ip}>"


class BannedIps(SQLModel, table=True):
    __tablename__ = "banned_ips"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )
    ip: str

    # Foreign Key to User
    userUid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional[User] = Relationship(back_populates="bannedIps")

    def __repr__(self) -> str:
        return f"<BannedIp {self.ip}>"


class VerifiedEmail(SQLModel, table=True):
    __tablename__ = "verified_emails"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )
    email: EmailStr = Field(nullable=False, unique=True, index=True, max_length=100)
    verifiedAt: datetime = Field(default_factory=datetime.utcnow)

    # Foreign Key to User
    userUid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional[User] = Relationship(back_populates="verifiedEmails")

    def __repr__(self) -> str:
        return f"<VerifiedEmail {self.email}>"


class Card(SQLModel, table=True):
    __tablename__ = "cards"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )
    cardNumber: Optional[PaymentCardNumber] = Field(nullable=True)
    expirationDate: Optional[date] = Field(nullable=True)
    cvv: Optional[str] = Field(nullable=True, max_length=3)

    valid: bool = Field(default=False)

    userUid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional[User] = Relationship(back_populates="cards")

    @property
    def cardBrand(self) -> Optional[PaymentCardBrand]:
        if self.cardNumber:
            return self.cardNumber.brand
        return None

    @property
    def cardMaskedNumber(self) -> Optional[str]:
        if self.cardNumber:
            return self.cardNumber.masked
        return None

    @property
    def expired(self) -> bool:
        if self.expirationDate:
            return self.expirationDate < date.today()
        return False

    def __repr__(self) -> str:
        return f"<Card {self.cardNumber}>"
