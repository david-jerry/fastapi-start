import uuid
from sqlalchemy import Column
from sqlmodel import Relationship, SQLModel, Field
import sqlalchemy.dialects.postgresql as pg
from typing import Optional, TYPE_CHECKING
from datetime import datetime


if TYPE_CHECKING:
    from src.apps.accounts.models import User

from .schemas import TransactionStatus, TransactionPaymentType


# TransactionHistory model
class TransactionHistory(SQLModel, table=True):
    __tablename__ = "transactions"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional["User"] = Relationship(back_populates="transactions")
    domain: str

    amount: float
    transaction_type: TransactionPaymentType = TransactionPaymentType.FUNDING
    status: TransactionStatus = TransactionStatus.PENDING  # Default status
    recipient_bank_name: str
    recipient_account_number: str
    recipient_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )
