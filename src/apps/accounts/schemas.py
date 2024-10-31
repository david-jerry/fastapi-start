import uuid

from fastapi import File, UploadFile
from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, FileUrl, IPvAnyAddress, constr, model_validator, root_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic_extra_types.routing_number import ABARoutingNumber
from pydantic_extra_types.payment import PaymentCardBrand, PaymentCardNumber
from pydantic_extra_types.country import CountryInfo

from datetime import date, datetime
from typing import Optional, List, Annotated

from src.apps.accounts.enums import UserGender, UserMaritalStatus


class LocationSchema(BaseModel):
    ip: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    country_calling_code: Optional[str] = None
    currency: Optional[str] = None
    in_eu: bool = False


class AccessToken(BaseModel):
    message: str
    access_token: str
    user: Optional["UserRead"] = None

class Message(BaseModel):
    message: str
    error_code: str


class ConflictingIpMessage(BaseModel):
    message: str
    ip: str
    error_code: str


class DeleteMessage(BaseModel):
    message: str

class Token(BaseModel):
    message: str = None
    code: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional["UserRead"] = None


class Verification(BaseModel):
    message: str
    code: str


class UserBaseSchema(BaseModel):
    firstName: Annotated[Optional[str], constr(max_length=255)] = None  # First name with max length constraint
    lastName: Annotated[Optional[str], constr(max_length=255)] = None  # Last name with max length constraint
    companyName: Annotated[Optional[str], constr(max_length=255)] = None  # Last name with max length constraint
    phoneNumber: Annotated[Optional[str], constr(min_length=10, max_length=14)] = None  # Phone number with length constraints
    dob: Optional[date] = None
    gender: Optional[UserGender] = UserGender.OTHERS  # Assuming it's a string or replace with an Enum
    maritalStatus: Optional[UserMaritalStatus] = UserMaritalStatus.SINGLE  # Assuming it's a string or replace with an Enum

    class Config:
        from_attributes = True  # Allows loading from ORM models like SQLModel


class UserRead(UserBaseSchema):
    uid: uuid.UUID
    email: EmailStr  = None # Email with validation
    image: Optional[str] = None
    joined: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    country: Optional[str] = None
    countryCode: Optional[str] = None
    countryCallingCode: Optional[str] = None
    currency: Optional[str] = None
    inEu: bool = False

    isBlocked: bool = False
    isCompany: bool = False
    isSuperuser: bool = False

    verifiedEmails: List["VerifiedEmailRead"] = []
    knownIps: List["KnownIpsRead"] = []
    bannedIps: List["BannedIpsRead"] = []
    cards: List["CardRead"] = []

    age: Optional[int] = None

    @staticmethod
    def calculate_age(dob: Optional[datetime]) -> int:
        if dob:
            today = datetime.today().date()
            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
            return age
        return 0

    @classmethod
    def from_orm(cls, user):
        user_dict = user.dict()
        user_dict["age"] = cls.calculate_age(user.dob)
        return cls(**user_dict)

class UserCreateOrLoginSchema(BaseModel):
    email: EmailStr  # Email with validation
    password: Annotated[str, constr(min_length=6)]


class UserUpdateSchema(UserBaseSchema):
    pass


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: Annotated[Optional[str], constr(min_length=6)]
    confirm_new_password: Annotated[Optional[str], constr(min_length=6)]


class VerifiedEmailBase(BaseModel):
    email: EmailStr


class VerifiedEmailCreate(VerifiedEmailBase):
    pass


class VerifiedEmailRead(VerifiedEmailBase):
    uid: uuid.UUID
    verifiedAt: datetime
    userUid: uuid.UUID

    class Config:
        from_attributes = True


class IpCreateSchema(BaseModel):
    ip: str


class KnownIpsRead(BaseModel):
    uid: uuid.UUID
    ip: str
    userUid: uuid.UUID

    class Config:
        from_attributes = True


class BannedIpsRead(BaseModel):
    uid: uuid.UUID
    ip: str
    userUid: uuid.UUID

    class Config:
        from_attributes = True


# Pydantic model for Card
class CardCreateSchema(BaseModel):
    cardNumber: PaymentCardNumber
    expirationDate: date
    cvv: Annotated[str, constr(min_length=3, max_length=3)]


class CardRead(BaseModel):
    uid: uuid.UUID = Field(default_factory=uuid.uuid4)
    cardNumber: Optional[PaymentCardNumber]
    cvv: Optional[str]
    expirationDate: Optional[date]

    valid: bool = Field(default=False)

    userUid: Optional[uuid.UUID]

    cardBrand: Optional[PaymentCardBrand] = None
    cardMaskedNumber: Optional[str] = None
    expired: bool = False

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    def compute_additional_properties(cls, values):
        card_number: Optional[PaymentCardNumber] = values.get("cardNumber")
        expiration_date: date = values.get("expirationDate")

        if card_number:
            values["cardBrand"] = card_number.brand
            values["cardMaskedNumber"] = card_number.masked

        if expiration_date:
            values["expired"] = expiration_date < date.today()
        else:
            values["expired"] = False

        return values
