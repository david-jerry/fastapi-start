from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import AnyHttpUrl, EmailStr, FileUrl, IPvAnyAddress
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
import uuid


# User Specific Models
class Testimonial(SQLModel, table=True):
    __tablename__ = "testimonials"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str
    position: str
    company: str = Field(unique=True)
    image: Optional[str]
    testimony: str
    rating: int
    domain: str = Field(default="https://jeremiahedavid.online")

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    def __repr__(self) -> str:
        return f"<Testimonial {self.company}>"
