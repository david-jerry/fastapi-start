from decimal import Decimal
import random
import uuid
import requests
import yfinance as yf
from yahooquery import Screener

import pandas as pd
import ccxt.async_support as ccxt

from datetime import datetime, timedelta
from typing import Annotated, Any, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# from src.app.auth.mails import send_card_pin, send_new_bank_account_details
from src.apps.accounts.dependencies import does_ip_exist, get_ip_address, get_location
from src.apps.accounts.models import BannedIps, Card, KnownIps, User, VerifiedEmail
from src.apps.portfolios.schemas import Ticker, TickerData
from src.db.cloudinary import upload_image
from src.db.db import get_session
from src.db.redis import store_allowed_ip, store_verification_code
from src.errors import InsufficientPermission, InvalidCredentials, PasswordsDoNotMatch, ProxyConflict, UnknownIpConflict, UserAlreadyExists, UserNotFound
from src.utils.hashing import create_access_token, generate_verification_code, generateHashKey, verifyHashKey
from src.utils.logger import LOGGER
from src.config.settings import Config

binance = ccxt.binance({
    "apiKey": Config.BINANCE_API,
    "secret": Config.BINANCE_SECRET
})

htx = ccxt.htx({
    "apiKey": Config.HTX_API,
    "secret": Config.HTX_SECRET
})

bitfinex = ccxt.bitfinex({
    "apiKey": Config.BITFINEX_API,
    "secret": Config.BITFINEX_SECRET
})

bybit = ccxt.bybit({
    "apiKey": Config.BYBIT_API,
    "secret": Config.BYBIT_SECRET
})

kraken = ccxt.kraken({
    "apiKey": Config.KRAKEN_API,
    "secret": Config.KRAKEN_SECRET
})


class PortfolioService:
    async def get_tickers(self, crypto: bool):
        s = Screener()
        if crypto:
            data = s.get_screeners('all_cryptocurrencies_us', count=250)
            quotes = data['all_cryptocurrencies_us']['quotes']
        else:
            data = s.get_screeners(['most_actives', 'day_gainers'], count=250)
            quotes = data['day_gainers']['quotes']

        res: List[Ticker] = []
        for q in quotes:
            ticker = yf.Ticker(q["symbol"])
            data = ticker.history(period="1mo", interval="15m")
            datas = []

            for d in data:
                dd = TickerData(
                    date=d["Datetime"],
                    open=d["Open"],
                    close=d["Close"]
                )
                datas.append(dd)

            rd = Ticker(
                symbol=q["symbol"],
                marketCapital=q["marketCap"],
                volume=data[-0]["Volume"],
                open=data[-0]["Open"],
                close=data[-0]["Close"],
                logo=ticker.info.get("logo_url", None),
                graphData=datas,
            )
            res.append(rd)

        return res

    async def buy_asset(self, symbol: str, amount: Decimal, user: User, exchange: any, session: AsyncSession):
        pass

    async def sell_asset(self, symbol: str, amount: Decimal, user: User, exchange: any, session: AsyncSession):
        pass

    async def arbitrage_run(self, symbol: str, duration: int, user: User, session: AsyncSession):
        pass

    async def arbitrage_stop(self, symbol: str, user: User, run_id: str, session: AsyncSession):
        pass

    async def copy_trade(self, symbol: str, duration: int, user: User, session: AsyncSession):
        pass

    async def subscribe(self, user: User, session: AsyncSession):
        pass

    async def unsubscribe(self, user: User, session: AsyncSession):
        pass

    async def create_portfolio(self, user: User, session: AsyncSession):
        pass

    async def stake_asset(self, form_data: dict, user: User, session: AsyncSession):
        pass

    async def withdraw_from_portfolio(self, portfolio_uid: uuid.UUID, user: User, session: AsyncSession):
        pass

    async def withdraw_stakes(self, stake_uid: uuid.UUID, user: User, session: AsyncSession):
        pass
