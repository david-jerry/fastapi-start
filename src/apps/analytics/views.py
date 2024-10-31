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
from src.apps.analytics.models import Analytics, PageView, ButtonsClicked
from src.apps.analytics.schemas import AnalyticsRead, CreateOrUpdateAnalytics, CreateOrUpdatePageView
from src.db.db import get_session
from src.apps.accounts.services import UserService
from src.config.settings import Config
from src.errors import FAQNotFound, InsufficientPermission
from src.utils.logger import LOGGER

session = Annotated[AsyncSession, Depends(get_session)]
user_service = UserService()
analysis_router = APIRouter()

current_time = datetime.utcnow()
one_hour_ago = current_time - timedelta(hours=1)

@analysis_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AnalyticsRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_analytics(request: Request, form_data: Annotated[CreateOrUpdatePageView, Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    pathname = request.headers.get("pathname")
    ip = get_ip_address(request)

    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Analytics).where(Analytics.domain == domain).where(Analytics.createdAt >= one_hour_ago))
    analytics_exists = db_result.first()

    if analytics_exists is None:
        new_analytics = Analytics(pathname=pathname, domain=domain)
        session.add(new_analytics)

        new_page = PageView(ip=ip, timeSpentInSeconds=form_data.timeSpendInSeconds, analytics=new_analytics, analyticsUid=new_analytics.uid)
        session.add(new_page)

        new_button = ButtonsClicked(buttonName=form_data.buttonsClicked, pageView=new_page, pageViewUid=new_page.uid)
        session.add(new_button)
        await session.commit()

        return new_analytics

    db_result = await session.exec(select(PageView).where(PageView.analyticsUid == analytics_exists.uid).where(PageView.date >= one_hour_ago))
    page_view_exists = db_result.first()
    if page_view_exists:
        if form_data.buttonsClicked is not None:
            new_button = ButtonsClicked(buttonName=form_data.buttonsClicked)
            await session.add(new_button)
            await session.commit()
            await session.refresh(analytics_exists)

        if form_data.ip is not None and form_data.ip != page_view_exists.ip:
            page_view_exists.ip = form_data.ip
            await session.commit()
            await session.refresh(analytics_exists)

        if form_data.timeSpendInSeconds is not None and form_data.timeSpendInSeconds != page_view_exists.timeSpentInSeconds:
            page_view_exists.timeSpentInSeconds = form_data.timeSpendInSeconds
            await session.commit()
            await session.refresh(analytics_exists)



@analysis_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[AnalyticsRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_all_analytics(request: Request, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"
    page = await paginate(session, select(Analytics).where(Analytics.domain==domain).order_by(Analytics.createdAt))
    return page.model_dump()

