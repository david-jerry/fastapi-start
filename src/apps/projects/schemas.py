from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import UploadFile
from pydantic import BaseModel, Field, IPvAnyAddress


class ProjectsRead(BaseModel):
    uid: uuid.UUID
    name: str
    description: str
    clientName: Optional[str]
    domain: str = Field(default="https://jeremiahedavid.online")
    existingLink: Optional[str]

    images: List["ProjectImageRead"]
    stacks: List["ProjectStacksRead"]

    createdAt: datetime

    class Config:
        from_attributes = True


class CreateOrUpdateProjects(BaseModel):
    name: Optional[str]
    description: Optional[str]
    completed: bool = False
    clientName: Optional[str] = None
    stacks: str
    existingLink: Optional[str] = None
    images: List["CreateOrUpdateProjectImages"]

class UpdateProjects(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    completed: bool = False
    clientName: Optional[str] = None
    stacks: str
    existingLink: Optional[str] = None
    images: List["CreateOrUpdateProjectImages"]

class ProjectImageRead(BaseModel):
    image: str

    class Config:
        from_attributes = True


class CreateOrUpdateProjectImages(BaseModel):
    image: UploadFile


class ProjectStacksRead(BaseModel):
    name: str

    class Config:
        from_attributes = True


class CreateOrUpdateProjectStacks(BaseModel):
    name: str
