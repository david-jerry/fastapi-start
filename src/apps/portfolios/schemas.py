from datetime import datetime, time
from decimal import Decimal
from typing import Annotated, List, Optional
import uuid
from pydantic import BaseModel, condecimal


class Ticker(BaseModel):
    symbol: str
    logo: Optional[str]
    totalSupply: Decimal
    marketCapital: Decimal
    volume: Decimal
    open: Decimal
    close: Decimal
    graphData: List["TickerData"]

class TickerData(BaseModel):
    date: datetime
    open: Decimal
    close: Decimal


class PortfolioBase(BaseModel):
    name: str
    currency: str


class PortfolioRead(PortfolioBase):
    uid: uuid.UUID
    name: str
    currency: str

    userUid: Optional[uuid.UUID]
    
    symbols: List["SymbolsRead"]
    shares: List["SharesRead"]
    stakings: List["StakingRead"]
    copyTrades: List["CopyTradeRead"]
    arbitrages: List["ArbitrageRead"]

    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class SymbolsRead(BaseModel):
    uid: uuid.UUID
    name: str
    symbol: str
    logo: str
    lastPrice: Decimal
    change: Decimal
    totalSupply: Decimal
    marketTime: time
    marketCap: Decimal
    volume: Decimal
    updatedAt: datetime


class CreateShares(BaseModel):
    purchasePrice: Decimal
    numberOfShares: int
    lowLimit: Decimal
    highLimit: Decimal
    symbolUid: Optional[uuid.UUID]


class SharesRead(BaseModel):
    uid: uuid.UUID
    purchasePrice: Decimal
    numberOfShares: int
    lowLimit: Decimal
    highLimit: Decimal
    symbolUid: Optional[uuid.UUID]
    portfolioUid: Optional[uuid.UUID]
    createdAt: datetime
    updatedAt: datetime


class CreateStaking(BaseModel):
    amountStaked: Decimal
    symbolUid: Optional[uuid.UUID]


class StakingRead(BaseModel):
    uid: uuid.UUID
    amountStaked: Decimal
    interestRate: int
    earnings: Decimal
    duration: Decimal
    symbolUid: Optional[uuid.UUID]
    portfolioUid: Optional[uuid.UUID]
    createdAt: datetime


class CreateArbitrage(BaseModel):
    leverage: int = 20
    riskPerTradePercentage: int = 2
    riskRewardRatio: int = 2
    stopLossPercent: Decimal = 0.2
    don_max_period: int = 12
    request_internal_seconds: int = 30
    symbolUid: Optional[uuid.UUID]


class ArbitrageRead(BaseModel):
    uid: uuid.UUID
    leverage: Optional[int]
    riskPerTradePercentage: Optional[int]
    riskRewardRatio: Optional[int]
    stopLossPercent: Decimal = 0.2
    don_max_period: Optional[int]
    request_internal_seconds: Optional[int]
    earnings: Decimal
    symbolUid: Optional[uuid.UUID]
    portfolioUid: Optional[uuid.UUID]
    createdAt: datetime


class CreateCopyTrade(BaseModel):
    watchedWalletAddress: str
    walletAddress: str
    percentToTrade: Decimal = 0.04
    symbolUid: Optional[uuid.UUID]


class CopyTradeRead(BaseModel):
    uid: uuid.UUID
    watchedWalletAddress: str
    walletAddress: str
    percentToTrade: Decimal = 0.04
    active: bool
    earnings: Decimal
    symbolUid: Optional[uuid.UUID]
    portfolioUid: Optional[uuid.UUID]
    createdAt: datetime

