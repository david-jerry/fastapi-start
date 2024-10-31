from datetime import datetime, timedelta
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Body, Depends, Path, Request, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.apps.accounts.dependencies import get_current_user, get_ip_address
from src.apps.accounts.models import User
from src.apps.accounts.schemas import ConflictingIpMessage, DeleteMessage, Message
from src.apps.faqs.models import FAQs
from src.apps.faqs.schemas import CreateOrUpdateFAQ, ReadFAQ
from src.db.db import get_session
from src.apps.accounts.services import UserService
from src.config.settings import Config
from src.errors import FAQNotFound, InsufficientPermission
from src.utils.logger import LOGGER

session = Annotated[AsyncSession, Depends(get_session)]
user_service = UserService()
faq_router = APIRouter()

@faq_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Page[ReadFAQ],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_faq(request: Request, form_data: Annotated[CreateOrUpdateFAQ, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    data = form_data
    form_dict = data.model_dump()
    new_faq = FAQs(**form_dict, domain=domain)
    session.add(new_faq)
    await session.commit()

    page = await paginate(session, select(FAQs).where(FAQs.domain==domain).order_by(FAQs.question, FAQs.createdAt))
    return page.model_dump()

@faq_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[ReadFAQ],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_all_faqs(request: Request, session: AsyncSession = Depends(get_session)):
    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"
    page = await paginate(session, select(FAQs).where(FAQs.domain==domain).order_by(FAQs.question, FAQs.createdAt))
    return page.model_dump()

@faq_router.patch(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=Page[ReadFAQ],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_faqs(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique faq uid")], form_data: Annotated[CreateOrUpdateFAQ, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(FAQs).where(FAQs.domain == domain).where(FAQs.uid==uid))
    faq_to_update = db_result.first()

    if faq_to_update is None:
        raise FAQNotFound()

    form_data_dict = form_data.model_dump()

    for k, v in form_data_dict.items():
        if v is not None:
            setattr(faq_to_update, k, v)

    await session.commit()
    await session.refresh(faq_to_update)

    page = await paginate(session, select(FAQs).where(FAQs.domain==domain).order_by(FAQs.question, FAQs.createdAt))
    return page.model_dump()

@faq_router.delete(
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
async def delete_faq(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique faq uid")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(FAQs).where(FAQs.domain == domain).where(FAQs.uid==uid))
    faq_to_delete = db_result.first()

    await session.delete(faq_to_delete)
    await session.commit()

    return {
        "message": f"{faq_to_delete.question} has been deleted successfully"
    }

