from datetime import datetime, timedelta
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Path, Request, UploadFile, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.apps.accounts.dependencies import get_current_user, get_ip_address
from src.apps.accounts.models import User
from src.apps.accounts.schemas import ConflictingIpMessage, DeleteMessage, Message
from src.apps.testimonials.models import Testimonial
from src.apps.testimonials.schemas import CreateOrUpdateTestimonial, ReadTestimonial
from src.apps.testimonials.service import createImageUrl
from src.db.db import get_session
from src.apps.accounts.services import UserService
from src.config.settings import Config
from src.errors import FAQNotFound, InsufficientPermission, TestimonialNotFound
from src.utils.logger import LOGGER

session = Annotated[AsyncSession, Depends(get_session)]
user_service = UserService()
testimonial_router = APIRouter()

@testimonial_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Page[ReadTestimonial],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_testimonial(request: Request, background_tasks: BackgroundTasks, form_data: Annotated[CreateOrUpdateTestimonial, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    data = form_data
    form_dict = data.model_dump()
    image = form_dict.pop("image")
    new_testimony = Testimonial(**form_dict, domain=domain)
    if image is not None:
        background_tasks.add_task(createImageUrl, new_testimony, image, session)

    session.add(new_testimony)
    await session.commit()
    page = await paginate(session, select(Testimonial).where(Testimonial.domain==domain).order_by(Testimonial.company, Testimonial.createdAt))
    return page.model_dump()

@testimonial_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[ReadTestimonial],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_all_testimonial(request: Request, session: AsyncSession = Depends(get_session)):
    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"
    page = await paginate(session, select(Testimonial).where(Testimonial.domain==domain).order_by(Testimonial.company, Testimonial.createdAt))
    return page.model_dump()

@testimonial_router.patch(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=Page[ReadTestimonial],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_testimonial(request: Request, background_tasks: BackgroundTasks, uid: Annotated[uuid.UUID, Path(title="Unique faq uid")], form_data: Annotated[CreateOrUpdateTestimonial, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Testimonial).where(Testimonial.domain == domain).where(Testimonial.uid==uid))
    testimony_to_update = db_result.first()

    if testimony_to_update is None:
        raise TestimonialNotFound()

    form_data_dict = form_data.model_dump()

    image = form_data_dict.pop("image")
    if image is not None:
        background_tasks.add_task(createImageUrl, testimony_to_update, image, session)

    for k, v in form_data_dict.items():
        if v is not None:
            setattr(testimony_to_update, k, v)

    await session.commit()
    await session.refresh(testimony_to_update)

    page = await paginate(session, select(Testimonial).where(Testimonial.domain==domain).order_by(Testimonial.company, Testimonial.createdAt))
    return page.model_dump()

@testimonial_router.delete(
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
async def delete_testimonial(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique faq uid")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Testimonial).where(Testimonial.domain == domain).where(Testimonial.uid==uid))
    testimony_to_delete = db_result.first()

    await session.delete(testimony_to_delete)
    await session.commit()

    return {
        "message": f"{testimony_to_delete.company} has been deleted successfully"
    }
