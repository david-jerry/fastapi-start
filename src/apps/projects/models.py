from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import AnyHttpUrl, EmailStr, FileUrl, IPvAnyAddress
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
import uuid


# User Specific Models
class ProjectStacksLink(SQLModel, table=True):
    projectUid: uuid.UUID | None = Field(default=None, foreign_key="projects.uid", primary_key=True)
    stackUid: uuid.UUID | None = Field(default=None, foreign_key="project_stacks.uid", primary_key=True)


class Projects(SQLModel, table=True):
    __tablename__ = "projects"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str = Field(unique=True)
    description: str
    clientName: Optional[str] = Field(nullable=True, default_factory=None)
    domain: str = Field(default="https://jeremiahedavid.online")
    completed: bool = Field(default=False)
    existingLink: Optional[str] = Field(nullable=True, default_factory=None)

    images: List["ProjectImages"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    stacks: List["ProjectStacks"] = Relationship(
        back_populates="projects",
        link_model=ProjectStacksLink,
    )

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    def __repr__(self) -> str:
        return f"<Projects {self.name}>"


class ProjectImages(SQLModel, table=True):
    __tablename__ = "project_images"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    image: str = Field(default="https://placeholder.co/400")
    projectUid: Optional[uuid.UUID] = Field(default=None, foreign_key="projects.uid")
    project: Optional[Projects] = Relationship(back_populates="images")

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    def __repr__(self) -> str:
        return f"<ProjectImages {self.name}>"


class ProjectStacks(SQLModel, table=True):
    __tablename__ = "project_stacks"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str
    projects: List[Projects] = Relationship(
        back_populates="stacks",
        link_model=ProjectStacksLink,
    )

    createdAt: date = Field(
        default_factory=date.today,
        sa_column=Column(pg.TIMESTAMP, default=date.today),
    )

    def __repr__(self) -> str:
        return f"<ProjectImages {self.name}>"
