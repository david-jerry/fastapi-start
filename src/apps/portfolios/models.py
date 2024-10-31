from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlmodel import Field, Relationship, SQLModel, Column
import sqlalchemy.dialects.postgresql as pg

if TYPE_CHECKING:
    from src.apps.accounts.models import User


class PortfolioSymbolLink(SQLModel, table=True):
    portfolioUid: uuid.UUID | None = Field(default=None, foreign_key="portfolio.uid", primary_key=True)
    symbolUid: uuid.UUID | None = Field(default=None, foreign_key="portfolio_symbols.uid", primary_key=True)


class Portfolio(SQLModel, table=True):
    __tablename__ = "portfolio"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str
    currency: str = Field(default="USD")
    balance: Decimal = Field(default=0.00, decimal_places=2)
    earnings: Decimal = Field(default=0.00, decimal_places=2)

    userUid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional[User] = Relationship(back_populates="portfolios")

    symbols: List["Symbols"] = Relationship(
        back_populates="portfolios",
        link_model=PortfolioSymbolLink,
    )
    shares: List["Shares"] = Relationship(
        back_populates="portfolio",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    stakings: List["Staking"] = Relationship(
        back_populates="portfolio",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    arbitrages: List["ArbitrageRecords"] = Relationship(
        back_populates="symbol",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    copyTrades: List["CopyTrading"] = Relationship(
        back_populates="portfolio",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )

    createdAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )
    updatedAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )


class Symbols(SQLModel, table=True):
    __tablename__ = "portfolio_symbols"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    name: str
    symbol: str
    logo: Optional[str]
    lastPrice: Decimal = Field(default=0.00, decimal_places=6)
    change: Decimal
    totalSupply: Decimal
    marketTime: time
    marketCap: Decimal
    volume: Decimal

    portfolios: List[Portfolio] = Relationship(
        back_populates="symbols",
        link_model=PortfolioSymbolLink,
    )
    shares: List["Shares"] = Relationship(
        back_populates="symbol",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    stakings: List["Staking"] = Relationship(
        back_populates="symbol",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    arbitrages: List["ArbitrageRecords"] = Relationship(
        back_populates="symbol",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    copyTrades: List["CopyTrading"] = Relationship(
        back_populates="symbol",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )

    updatedAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )


class Shares(SQLModel, table=True):
    __tablename__ = "shares"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    purchasePrice: Decimal = Field(default=0.00, decimal_places=2)
    numberOfShares: int = Field(default=1)
    lowLimit: Decimal = Field(default=0.00, decimal_places=2)
    highLimit: Decimal = Field(default=0.00, decimal_places=2)

    symbolUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio_symbols.uid")
    symbol: Optional[Symbols] = Relationship(back_populates="shares")
    portfolioUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio.uid")
    portfolio: Optional[Portfolio] = Relationship(back_populates="shares")

    createdAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )
    updatedAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )


class Staking(SQLModel, table=True):
    __tablename__ = "staking"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    amountStaked: Decimal = Field(default=0.000000, decimal_places=6)
    interestRate: Decimal = Field(default=0.04, decimal_places=2)
    earnings: Decimal = Field(default=0.000000, decimal_places=6)
    duration: int = Field(default=30)

    symbolUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio_symbols.uid")
    symbol: Optional[Symbols] = Relationship(back_populates="stakings")
    portfolioUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio.uid")
    portfolio: Optional[Portfolio] = Relationship(back_populates="stakings")

    createdAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )


class ArbitrageRecords(SQLModel, table=True):
    # https://medium.com/@crjameson/how-to-write-an-automated-crypto-perp-trading-bot-in-python-with-less-than-100-lines-of-code-e6503910fadb
    __tablename__ = "arbitrage"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    lowestAmount: Decimal = Field(default=0.000000, decimal_places=6)
    highestAmount: Decimal = Field(default=0.000000, decimal_places=6)
    exchange: str
    leverage: int = Field(default=20)
    riskPerTradePercentage: int = Field(default=2)
    riskRewardRatio: int = Field(default=2)
    stopLossPercent: Decimal = Field(default=0.2, decimal_places=2)
    earnings: Decimal = Field(default=0.000000, decimal_places=6)

    # the length of the queue is the period of the donchian channel
    # 120 means we look at the last 120 prices, one request every 30 seconds = 1h timeframe
    don_max_period: int = Field(default=12)
    request_interval_seconds: int = Field(default=30)

    symbolUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio_symbols.uid")
    symbol: Optional[Symbols] = Relationship(back_populates="arbitrages")
    portfolioUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio.uid")
    portfolio: Optional[Portfolio] = Relationship(back_populates="arbitrages")

    createdAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )

    @property
    def takeProfitPercent(self):
        return self.stopLossPercent * self.riskRewardRatio


class CopyTrading(SQLModel, table=True):
    __tablename__ = "copy_trading"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, primary_key=True, unique=True, nullable=False, default=uuid.uuid4
        )
    )

    symbolUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio_symbols.uid")
    symbol: Optional[User] = Relationship(back_populates="copyTrades")

    watchedWalletAddress: str

    walletAddress: str
    network: str #bnb, eth

    percentToTrade: Decimal = Field(default=0.04, decimal_places=6)
    earnings: Decimal = Field(default=0.000000, decimal_places=6)
    active: bool = Field(default=True)

    symbolUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio_symbols.uid")
    symbol: Optional[Symbols] = Relationship(back_populates="copyTrades")
    portfolioUid: Optional[uuid.UUID] = Field(default=None, foreign_key="portfolio.uid")
    portfolio: Optional[Portfolio] = Relationship(back_populates="copyTrades")

    createdAt: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
    )









