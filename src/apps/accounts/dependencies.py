import uuid
import aiohttp
import requests
from typing import Any, List, Annotated, Optional

from sqlmodel import select

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession

from src.apps.accounts.models import BannedIps, KnownIps, User
from src.apps.accounts.schemas import LocationSchema
from src.db.db import get_session
from src.config.settings import Config
from src.db.redis import token_in_blocklist
from src.errors import AccessTokenRequired, BannedIp, InsufficientPermission, InvalidToken, RefreshTokenRequired, UnknownIpConflict, UserBlocked, UserNotFound
from src.utils.hashing import decode_token
from src.utils.logger import LOGGER

oauth2_bearer = OAuth2PasswordBearer(tokenUrl=f"/{Config.VERSION}/auth/login")
db_dependency = Annotated[AsyncSession, Depends(get_session)]
oauth2_bearer_dependency = Annotated[str, Depends(oauth2_bearer)]

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)

        token = creds.credentials

        token_data = decode_token(token)

        if token_data is None:
            raise InvalidToken()

        token_is_valid = self.token_valid(token)
        blocked = await token_in_blocklist(token_data["jti"])

        if not token_is_valid:
            raise InvalidToken()

        if blocked:
            raise InvalidToken()

        self.verify_token_data(token_data)

        return token_data

    def token_valid(self, token: oauth2_bearer_dependency) -> bool:  #str
        token_data = decode_token(token)
        return token_data is not None

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise AccessTokenRequired()


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise RefreshTokenRequired()


async def does_user_exist(email: Optional[str], uid: Optional[uuid.UUID], request: Request, session: Annotated[AsyncSession, Depends(get_session)]) -> User:
    if email is not None:
        db_result = await session.exec(select(User).where(User.email == email))
    else:
        db_result = await session.exec(select(User).where(User.uid == uid))

    user = db_result.first()
    if user is None:
        raise UserNotFound()

    await does_ip_exist(user, request, session)
    return user

async def get_location(ip: str) -> LocationSchema:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://ipapi.co/{ip}/json/') as response:
            response_data = await response.json()

    LOGGER.debug(response_data.get("in_eu"))

    location_data = {
        "ip": ip,
        "city": response_data.get("city"),
        "region": response_data.get("region"),
        "country": response_data.get("country_name"),
        "country_code": response_data.get("country_code"),
        "country_calling_code": response_data.get("country_calling_code"),
        "currency": response_data.get("currency"),
        "in_eu": True if response_data.get("in_eu") == "true" else False,
    }

    return LocationSchema(**location_data)

def get_ip_address(request: Request):
    ip = request.headers.get("next-ip")

    if ip is None and request.url.hostname in ["localhost", "api.jeremiahedavid.online", "api.jeremiahedavid.com.ng"]:
        ip = request.headers.get("X-Forwarded-For")
        if ip:
            ip = ip.split(',')[0].strip()  # Use the first IP in the chain (the client)
        else:
            ip = request.headers.get("X-Real-IP", request.client.host)

    return ip or "127.0.0.1"

async def does_ip_exist(user: User, request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    """
    This function checks if a given IP address exists in the database for a specific user.
    """
    ip = get_ip_address(request)

    db_result = await session.exec(select(KnownIps).where(KnownIps.userUid == user.uid).where(KnownIps.ip == ip))
    new_ip = db_result.first()

    LOGGER.debug(f"Does Ip Address Function: {new_ip}")

    if new_ip is None:
        raise UnknownIpConflict()

    banned_result = await session.exec(select(BannedIps).where(BannedIps.ip == ip).where(BannedIps.userUid == user.uid))
    banned_ip = banned_result.first()

    if banned_ip is not None:
        raise BannedIp()
    pass

async def get_current_user(token_details: Annotated[dict, Depends(AccessTokenBearer())], request: Request, session: Annotated[AsyncSession, Depends(get_session)]) -> User:
    user_email = token_details["user"]["email"]
    user = await does_user_exist(user_email, None, request, session)

    if user.isBlocked:
        raise UserBlocked()
    return user

async def permission_check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.isCompany or not current_user.isSuperuser:
        raise InsufficientPermission()
    return current_user
