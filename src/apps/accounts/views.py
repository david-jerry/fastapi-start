from datetime import datetime, timedelta
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Path, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from pydantic_extra_types.payment import PaymentCardNumber

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.apps.accounts.dependencies import AccessTokenBearer, RefreshTokenBearer, get_current_user, get_ip_address
from src.apps.accounts.enums import UserRole
from src.apps.accounts.models import Card, User
from src.db.db import get_session
from src.apps.accounts.schemas import AccessToken, CardCreateSchema, CardRead, ConflictingIpMessage, DeleteMessage, IpCreateSchema, Message, PasswordResetConfirmModel, PasswordResetRequestModel, Token, UserCreateOrLoginSchema, UserRead, UserUpdateSchema, Verification
from src.apps.accounts.services import UserService
from src.errors import BannedIp, CardAlreadyExists, CardNotFound, FormDataRequired, InsufficientPermission, InvalidCredentials, InvalidToken, PasswordsDoNotMatch, ProxyConflict, UnknownIpConflict, UserAlreadyExists, UserBlocked, UserNotFound
from src.config.settings import Config
from src.db.redis import (
    add_jti_to_blocklist,
    get_password_reset_code,
    get_verification_status,
    store_password_reset_code,
    store_verification_code,
)
from src.utils.hashing import create_access_token, decode_url_safe_token, generate_password_reset_code, generate_verification_code, generateHashKey, verifyHashKey
from src.utils.logger import LOGGER

session = Annotated[AsyncSession, Depends(get_session)]
user_service = UserService()
auth_router = APIRouter()
user_router = APIRouter()


@auth_router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=Verification, responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def register(request: Request, form_data: Annotated[UserCreateOrLoginSchema, Body()], permission: Optional[UserRole] = UserRole.COMPANY, session: AsyncSession = Depends(get_session)):
    code = await user_service.register_new_user(permission, form_data, request, session)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Account created successfully", "code": code}
    )

@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def login(request: Request, form_data: Annotated[UserCreateOrLoginSchema, Body(...)], session: AsyncSession = Depends(get_session)):
    user = await user_service.authenticate_user(form_data, request, session)
    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
        },
        expiry=timedelta(seconds=Config.ACCESS_TOKEN_EXPIRY),
    )
    refresh_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid)
        },
        refresh=True,
        expiry=timedelta(days=7),
    )
    code = None
    if len(user.verifiedEmails) < 1:
        code = generate_verification_code()
        await store_verification_code(user.uid, code)

        return {
            "message": "Please verify your email to get authenticated",
            "code": code,
        }

    return {
        "message": "Authenticated successfully",
        "code": code,
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@auth_router.post(
    "/verify-email/{token}",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def verify_email(request: Request, token: Annotated[str, Path], session: AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    user = await user_service.get_user_by_email_or_uid(email=user_email, session=session)
    if not user:
        raise UserNotFound()

    existing_email = next(
            (email for email in user.verifiedEmails if email.email == user_email), None
    )
    if existing_email:
        return {
            "message": "Email already verified",
            "user": user,
        }

    await user_service.verify_user_email(user_email, user, session)
    return {
        "message": "Email verified successfully",
        "user": user
    }

@auth_router.get(
    "/refresh_token",
    status_code=status.HTTP_200_OK,
    response_model=AccessToken,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_new_access_token(token_details: Annotated[dict, Depends(RefreshTokenBearer())], session: AsyncSession = Depends(get_session)):
    expiry_timestamp = token_details["exp"]
    user_email = token_details["user"]["email"]

    if datetime.fromtimestamp(expiry_timestamp).date() < datetime.now().date():
        raise InvalidToken()

    user = await user_service.get_user_by_email_or_uid(email=user_email, session=session)
    if user is None:
        raise UserNotFound()

    new_access_token = create_access_token(user_data=token_details["user"])
    return {
        "message": "AccessToken generated successfully",
        "access_token": new_access_token,
        "user": user
    }

@auth_router.get(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )

@auth_router.post(
    "/password-reset-request",
    status_code=status.HTTP_200_OK,
    response_model=Verification,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def password_reset_request(
    form_data: Annotated[PasswordResetRequestModel, Body(...)],
    session: AsyncSession = Depends(get_session),
):
    email = form_data.email
    user = await user_service.get_user_by_email_or_uid(email=email, session=session)
    code = generate_password_reset_code(email)
    await store_password_reset_code(user.uid, code)

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
            "code": code,
        },
        status_code=status.HTTP_200_OK,
    )

@auth_router.post(
    "/password-reset-confirm/{token}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def reset_account_password(
    token: Annotated[str, Path],
    background_tasks: BackgroundTasks,
    passwords: Annotated[PasswordResetConfirmModel, Body(...)],
    session: AsyncSession = Depends(get_session),
):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise PasswordsDoNotMatch()

    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    if not user_email:
        return JSONResponse(
            content={"message": "Error occurred during password reset."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    user = await user_service.get_user_by_email_or_uid(email=user_email, session=session)
    if not user:
        raise UserNotFound()

    data = UserUpdateSchema(password=new_password)

    await user_service.update_existing_user(user=user, background_tasks=background_tasks, form_data=data, session=session)

    return JSONResponse(
        content={"message": "Password reset Successfully"},
        status_code=status.HTTP_200_OK,
    )


# User Routes
@user_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[UserRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def all_users(request: Request, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isSuperuser:
        raise InsufficientPermission()
    page: Page[UserRead] = await paginate(session, select(User).where(User.uid != user.uid).order_by(User.firstName, User.companyName))
    return page.model_dump()

@user_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def me(request: Request, user: User = Depends(get_current_user)):
    return user

@user_router.get(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_user_profile(uid: Annotated[uuid.UUID, Path], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    user_to_fetch = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    return user_to_fetch

@user_router.patch(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_profile(uid: Annotated[uuid.UUID, Path(title="Unique user uid")],  background_tasks: BackgroundTasks, form_data: Annotated[UserUpdateSchema, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    LOGGER.debug(f"Form Data: {form_data}")
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()

    user_to_update = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    user = await user_service.update_existing_user(user_to_update, background_tasks, form_data, session)
    return user

@user_router.patch(
    "/{uid}/photo",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_profile_photo(uid: Annotated[uuid.UUID, Path(title="Unique user uid")],  background_tasks: BackgroundTasks, form_data: Annotated[UploadFile, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    LOGGER.debug(f"Form Data: {form_data}")
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()

    user_to_update = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    user = await user_service.update_image(background_tasks, user_to_update, form_data, session)
    return user

@user_router.patch(
    "/{uid}/change-password",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_profile_password(uid: Annotated[uuid.UUID, Path(title="Unique user uid")],  background_tasks: BackgroundTasks, form_data: PasswordResetConfirmModel, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    LOGGER.debug(f"Form Data: {form_data}")
    if user.uid != uid:
        raise InsufficientPermission()

    user_to_update = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    user = await user_service.update_existing_user_password(user_to_update, form_data, session)
    return user

@user_router.delete(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def delete_profile(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    user_to_remove = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    await user_service.remove_user(user_to_remove, session)
    return {
        "message": f"{user.companyName} has been deleted successfully"
    }

@user_router.post(
    "/{uid}/allow-ips",
    status_code=status.HTTP_201_CREATED,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_ip_address(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], form_data: Annotated[IpCreateSchema, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    user_to_add_ip = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    user = await user_service.add_allowed_ip(user_to_add_ip, form_data.ip, session)
    return {
        "message": f"{form_data.ip} added to known IPs"
    }

@user_router.post(
    "/{uid}/ban-ips",
    status_code=status.HTTP_201_CREATED,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def ban_new_ip_address(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], form_data: Annotated[IpCreateSchema, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    user_to_add_ip = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    user = await user_service.add_banned_ip(user_to_add_ip, form_data.ip, session)
    return {
        "message": f"{form_data.ip} banned successfully"
    }

@user_router.delete(
    "/{uid}/ban-ips/{ip}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def unban_new_ip_address(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], ip: Annotated[str, Path(title="Unique ip uid")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    user_to_add_ip = await user_service.get_user_by_email_or_uid(uid=uid, session=session)
    user = await user_service.remove_banned_ip(user_to_add_ip, ip, session)
    return {
        "message": f"{ip} has been unbanned successfully"
    }

@user_router.post(
    "/{uid}/cards",
    status_code=status.HTTP_201_CREATED,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_debit_card(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], form_data: Annotated[CardCreateSchema, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    user_to_add_card = await user_service.get_user_by_email_or_uid(uid=uid, session=session)

    db_result = await session.exec(select(Card).where(Card.cardNumber == form_data.cardNumber).where(Card.userUid==uid))
    card_to_update = db_result.first()

    if card_to_update is None:
        raise CardAlreadyExists()

    card = await user_service.register_new_card(user_to_add_card, form_data, session)
    return {
        "message": f"Your {card.cardBrand} Card - {card.cardMaskedNumber} has been added successfully"
    }

@user_router.patch(
    "/{uid}/cards/{cardNumber}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteMessage,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_debit_card(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], cardNumber: Annotated[PaymentCardNumber, Path(title="Unique debit card number")], form_data: Annotated[dict, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    db_result = await session.exec(select(Card).where(Card.cardNumber == cardNumber).where(Card.userUid==uid))
    card_to_update = db_result.first()

    if card_to_update is None:
        raise CardNotFound()

    card = await user_service.update_active_card(card_to_update, form_data, session)
    return {
        "message": f"Your {card.cardBrand} Card - {card.cardMaskedNumber} has been deactivated successfully"
    }

@user_router.get(
    "/{uid}/cards",
    status_code=status.HTTP_200_OK,
    response_model=Page[CardRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_all_debit_cards(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], cardNumber: Annotated[PaymentCardNumber, Path(title="Unique debit card number")], form_data: Annotated[dict, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid:
        raise InsufficientPermission()

    db_result = await paginate(session, select(Card).where(Card.cardNumber == cardNumber).where(Card.userUid==uid))
    page = db_result.model_dump()
    return page

@user_router.get(
    "/{uid}/cards/{cardNumber}",
    status_code=status.HTTP_200_OK,
    response_model=CardRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_debit_card(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique user uid")], cardNumber: Annotated[PaymentCardNumber, Path(title="Unique debit card number")], form_data: Annotated[dict, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.uid != uid and not user.isSuperuser:
        raise InsufficientPermission()
    db_result = await session.exec(select(Card).where(Card.cardNumber == cardNumber).where(Card.userUid==uid))
    card = db_result.first()

    if card is None:
        raise CardNotFound()

    return card

