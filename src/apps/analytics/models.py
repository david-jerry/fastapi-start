from datetime import date, datetime
from decimal import Decimal
from pydantic import AnyHttpUrl, EmailStr, FileUrl, IPvAnyAddress
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from typing import List, Optional
from pydantic_extra_types.phone_numbers import PhoneNumber


# User Specific Models
class Analytics(SQLModel, table=True):
    __tablename__ = "analytics"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    pathname: str = Field(nullable=False)
    domain: str = Field(default="https://jeremiahedavid.online")
    createdAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )

    # Relationships to track page views
    pageViews: List["PageView"] = Relationship(
        back_populates="analytics", sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )

    def __repr__(self) -> str:
        return f"<Analytics {self.pathname}>"


class PageView(SQLModel, table=True):
    __tablename__ = "page_views"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    ip: str = Field(nullable=False)
    buttonsClicked: List["ButtonsClicked"] = Relationship(
        back_populates="pageView", sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )  # Track buttons clicked
    timeSpentInSeconds: int = Field(default=0)  # Store time spent in seconds
    date: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(pg.TIMESTAMP, nullable=False))

    # Foreign Key to Analytics
    analyticsUid: Optional[uuid.UUID] = Field(default=None, foreign_key="analytics.uid")
    analytics: Optional["Analytics"] = Relationship(back_populates="pageViews")

    def __repr__(self) -> str:
        return f"<PageView {self.ip} - {self.date}>"


class ButtonsClicked(SQLModel, table=True):
    __tablename__ = "buttons_clicked"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    buttonName: Optional[str] = Field(default=None)

    pageViewUid: Optional[uuid.UUID] = Field(default=None, foreign_key="page_views.uid")
    pageView: Optional[PageView] = Relationship(back_populates="buttonsClicked")

    createdAt: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(pg.TIMESTAMP, nullable=False))
