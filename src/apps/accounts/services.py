import random
import uuid

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
from src.db.cloudinary import upload_image
from src.db.db import get_session
from src.db.redis import store_allowed_ip, store_verification_code
from src.errors import InsufficientPermission, InvalidCredentials, PasswordsDoNotMatch, ProxyConflict, UnknownIpConflict, UserAlreadyExists, UserNotFound
from src.utils.hashing import create_access_token, generate_verification_code, generateHashKey, verifyHashKey
from src.utils.logger import LOGGER
from src.config.settings import Config

from src.apps.accounts.schemas import CardCreateSchema, PasswordResetConfirmModel, Token, UserCreateOrLoginSchema, UserUpdateSchema


def update_profile(image: Annotated[bytes, UploadFile], session: AsyncSession, user: User) -> None:
    user.image = upload_image(image)
    session.commit()
    session.refresh(user)


class UserService:
    async def get_user_by_email_or_uid(self, email: Optional[str] = None, uid: Optional[uuid.UUID] = None, session: AsyncSession = Depends(get_session)) -> User:
        user = None
        if email is not None:
            statement=select(User).where(User.email == email)
            db_result = await session.exec(statement)
            user = db_result.first()
        elif uid is not None:
            statement=select(User).where(User.uid == uid)
            db_result = await session.exec(statement)
            user = db_result.first()
        return user

    async def verify_user_email(self, email: str, user: User, session: AsyncSession = Depends(get_session)) -> User:
        new_email = VerifiedEmail(email = email, userUid = user.uid, user = user)
        session.add(new_email)
        await session.commit()

    async def authenticate_user(self, form_data: UserCreateOrLoginSchema, request: Request, session: AsyncSession):
        user: Optional[User] = await self.get_user_by_email_or_uid(email=form_data.email, session=session)
        if user is None:
            raise UserNotFound()

        await does_ip_exist(user, request, session)

        valid_password = verifyHashKey(form_data.password, user.passwordHash)
        if not valid_password:
            raise InvalidCredentials()

        return user

    async def register_new_user(self, permission: str, form_data: UserCreateOrLoginSchema, request: Request, session: AsyncSession):
        user: Optional[User] = await self.get_user_by_email_or_uid(email=form_data.email, session=session)

        ip = get_ip_address(request)
        if ip is None:
            raise ProxyConflict()

        if user is not None:
            # code = None
            # if not user.verifiedEmails or len(user.verifiedEmails) < 1:
            #     code = generate_verification_code()
            #     await store_verification_code(user.uid, code)

            # return code
            raise UserAlreadyExists()

        data_dict = form_data.model_dump()
        new_user = User(**data_dict)
        new_user.passwordHash = generateHashKey(form_data.password)

        # create permissions
        if permission == "company":
            new_user.isCompany = True
        elif permission == "superuser":
            new_user.isCompany = True
            new_user.isSuperuser = True

        location= await get_location(ip)
        new_user.country = location.country
        new_user.countryCode = location.country_code
        new_user.countryCallingCode = location.country_calling_code
        new_user.inEu = location.in_eu
        new_user.currency = location.currency

        session.add(new_user)
        await session.commit()

        new_ip = KnownIps(ip=ip, user=new_user, userUid=new_user.uid)
        session.add(new_ip)
        await session.commit()

        await session.commit()
        await session.refresh(new_user)

        code = generate_verification_code()
        await store_verification_code(new_user.uid, code)


        return code

    async def update_existing_user(self, user: User, background_tasks: BackgroundTasks, form_data: Optional[UserUpdateSchema] = None, session: AsyncSession = Depends(get_session)):
        LOGGER.debug(f"Form Data: {form_data}")

        if form_data is not None:
            user_data = form_data.model_dump()
            password = user_data.pop("password")
            image: Annotated[bytes, UploadFile] = user_data.pop("image")

            if password is not None:
                user.passwordHash = generateHashKey(password)

            # if image is not None:
            #     background_tasks.add_task(update_profile, image, session, user)

            for k, v in user_data.items():
                if v is not None:
                    setattr(user, k, v)

        await session.commit()
        await session.refresh(user)
        return user

    async def update_existing_user_password(self, user: User, form_data: PasswordResetConfirmModel, session: AsyncSession = Depends(get_session)):
        LOGGER.debug(f"Form Data: {form_data}")

        if form_data.new_password != form_data.confirm_new_password:
            raise PasswordsDoNotMatch()

        user.passwordHash = generateHashKey(form_data.new_password)

        await session.commit()
        await session.refresh(user)
        return user

    async def register_new_card(self, user: User, form_data: CardCreateSchema, session: AsyncSession):
        data_dict = form_data.model_dump()
        new_card = Card(**data_dict, user=user, userUid=user.uid)
        session.add(new_card)
        await session.commit()
        await session.refresh(user)
        return new_card

    async def update_active_card(self, card: Card, form_data: dict, session: AsyncSession):
        LOGGER.debug(form_data)
        card_data = form_data
        for k, v in card_data.items():
            setattr(card, k, v)

        await session.commit()
        await session.refresh(card)
        return card

    async def update_image(self, background_tasks: BackgroundTasks, user: User, image: UploadFile, session: AsyncSession):
        background_tasks.add_task(update_profile, image, session, user)
        await session.commit()
        await session.refresh(user)
        return user

    async def remove_user(self, user: User, session: AsyncSession) -> None:
        await session.delete(user)
        await session.commit()
        return None

    async def add_allowed_ip(self, user: User, ip: str, session: AsyncSession):
        # add the new ip
        new_ip = KnownIps(ip=ip, user=user, userUid=user.uid)
        session.add(new_ip)
        await session.commit()

        # link the new ip to the user
        user.knownIps.append(new_ip)
        await session.commit()
        await session.refresh(user)
        return user

    async def add_banned_ip(self, user: User, ip: str, session: AsyncSession):
        # add the new ip
        new_ip = BannedIps(ip=ip, user=user, userUid=user.uid)
        session.add(new_ip)
        await session.commit()

        # link the new ip to the user
        user.knownIps.append(new_ip)
        await session.commit()
        await session.refresh(user)
        return user

    async def remove_banned_ip(self, user: User, ip: str, session: AsyncSession):
        # add the new ip
        db_result = await session.exec(select(BannedIps).where(BannedIps.ip == ip).where(BannedIps.userUid == user.uid))
        banned_ip = db_result.first()

        if banned_ip is not None:
            await session.delete(banned_ip)
            await session.commit()
        return None




