from datetime import datetime, timedelta
from decimal import Decimal
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
from src.apps.projects.models import Projects, ProjectImages, ProjectStacks, ProjectStacksLink
from src.apps.projects.schemas import CreateOrUpdateProjectImages, CreateOrUpdateProjects, CreateOrUpdateProjectStacks, ProjectsRead, UpdateProjects
from src.apps.projects.service import createImageUrl
from src.apps.requests.models import Milestones, RequestedServices, ServiceFeatures, Services
from src.apps.requests.schemas import CreateOrUpdateMilestones, CreateOrUpdateService, CreateOrUpdateServiceFeatures, CreateRequestedServices, RequestedServicesRead, ServicesRead, UpdateRequestedServices
from src.apps.requests.services import createFeatureImageUrl, get_random_decimal
from src.db.cloudinary import upload_image
from src.db.db import get_session
from src.apps.accounts.services import UserService
from src.config.settings import Config
from src.errors import FAQNotFound, InsufficientPermission, MilestoneNotFound, ProjectNotFound, RequestNotFound, ServiceNotFound
from src.utils.logger import LOGGER

session = Annotated[AsyncSession, Depends(get_session)]
user_service = UserService()
service_router = APIRouter()
request_router = APIRouter()


@service_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ServicesRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_service(request: Request, background_tasks: BackgroundTasks, form_data: Annotated[CreateOrUpdateService, Body(...)], features_data: Annotated[List[CreateOrUpdateServiceFeatures], Body(...)], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    data = form_data.model_dump()

    # first extract the stacks, if there is an existing stack add it to the list of stacks
    new_service = Services(**data, domain=domain)

    if len(features_data) > 0:
        for feature in features_data:
            feature_data_dict = feature.model_dump()
            image: UploadFile = feature_data_dict.pop("image")
            new_feature = ServiceFeatures(**feature_data_dict, service=new_service, serviceUid=new_service.uid)
            background_tasks.add_task(createFeatureImageUrl, new_feature, image, session)
            session.add(new_feature)
    session.add(new_service)
    await session.commit()
    await session.refresh(new_service)
    return new_service

@service_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[ServicesRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_all_services(request: Request, session: AsyncSession = Depends(get_session)):
    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"
    db_result = await session.exec(select(Services).where(Services.domain == domain).order_by(Services.name))
    return db_result.all()

@service_router.patch(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=List[ProjectsRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_service(request: Request, background_tasks: BackgroundTasks, uid: Annotated[uuid.UUID, Path(title="Unique service uid")], form_data: CreateOrUpdateService, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Services).where(Services.domain == domain).where(Services.uid==uid))
    service_to_update = db_result.first()

    if service_to_update is None:
        raise ServiceNotFound()

    form_data_dict = form_data.model_dump()

    for k, v in form_data_dict.items():
        # set new values if they are not none, has the keys "images" or "stacks" and the completed key value is not already what the existing project has
        if v is not None:
            setattr(service_to_update, k, v)

    await session.commit()
    await session.refresh(service_to_update)

    db_result = await session.exec(select(Services).where(Services.domain==domain).order_by(Services.name, Services.createdAt))
    return db_result.all()

@service_router.patch(
    "/{uid}/{featureUid}",
    status_code=status.HTTP_200_OK,
    response_model=Page[ProjectsRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_new_or_update_features(request: Request, background_tasks: BackgroundTasks, uid: Annotated[uuid.UUID, Path(title="Unique service uid")], form_data: Annotated[CreateOrUpdateServiceFeatures, Body(...)], featureUid: Annotated[Optional[uuid.UUID|str], Path(title="Unique feature uid|str")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Services).where(Services.domain == domain).where(Services.uid==uid))
    service = db_result.first()

    if service is None:
        raise ServiceNotFound()

    form_data_dict = form_data.model_dump()
    db_result = await session.exec(select(ServiceFeatures).where(ServiceFeatures.serviceUid == uid).where(ServiceFeatures.uid == featureUid))
    feature_to_update = db_result.first()

    if feature_to_update is None:
        image: UploadFile = form_data_dict.pop("image")
        new_feature = ServiceFeatures(**form_data_dict, service=service, serviceUid=service.uid)
        background_tasks.add_task(createFeatureImageUrl, new_feature, image, session)
        session.add(new_feature)
    else:
        for k, v in form_data_dict.items():
            # set new values if they are not none, has the keys "images" or "stacks" and the completed key value is not already what the existing project has
            if v is not None:
                setattr(feature_to_update, k, v)

    await session.commit()
    await session.refresh(service)

    db_service_result = await session.exec(select(Services).where(Services.domain==domain).order_by(Services.name))
    services = await db_service_result.all()
    return services

@service_router.delete(
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
async def delete_service(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique service uid")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Services).where(Services.domain == domain).where(Services.uid==uid))
    service_to_delete = db_result.first()

    await session.delete(service_to_delete)
    await session.commit()

    return {
        "message": f"{service_to_delete.name} has been deleted successfully"
    }

@request_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RequestedServicesRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def create_new_request(request: Request, form_data: Annotated[CreateRequestedServices, Body(...)], session: AsyncSession = Depends(get_session)):
    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    data = form_data.model_dump()

    services = data.pop("services")

    all_services = []
    total_cost: Decimal = 0.00

    for service in services:
        service_db_result = await session.exec(select(ServiceFeatures).where(ServiceFeatures.uid == service).where())
        saved_service = service_db_result.first()
        if saved_service is not None:
            random_charge = get_random_decimal(saved_service.minPrice , saved_service.maxPrice)
            total_cost += random_charge
            all_services.append(saved_service)

    # first extract the stacks, if there is an existing stack add it to the list of stacks
    new_request = RequestedServices(**data, domain=domain, totalCost=total_cost, services=all_services)
    session.add(new_request)
    await session.commit()
    return new_request

@request_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[RequestedServicesRead],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def get_all_requests(request: Request, session: AsyncSession = Depends(get_session)):
    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"
    page = await paginate(session, select(RequestedServices).where(RequestedServices.domain == domain).order_by(RequestedServices.createdAt.dsc()))
    return page.model_dump()

@request_router.patch(
    "/{uid}",
    status_code=status.HTTP_200_OK,
    response_model=RequestedServicesRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_request(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique request uid")], form_data: UpdateRequestedServices, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(RequestedServices).where(RequestedServices.domain == domain).where(RequestedServices.uid==uid))
    request_to_update = db_result.first()

    if request_to_update is None:
        raise RequestNotFound()

    form_data_dict = form_data.model_dump()

    for k, v in form_data_dict.items():
        # set new values if they are not none, has the keys "images" or "stacks" and the completed key value is not already what the existing project has
        if v is not None:
            setattr(request_to_update, k, v)

    await session.commit()
    await session.refresh(request_to_update)
    return request_to_update

@request_router.post(
    "/{uid}/milestones",
    status_code=status.HTTP_201_CREATED,
    response_model=RequestedServicesRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def add_milestones_to_request(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique request uid")], form_data: CreateOrUpdateMilestones, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(RequestedServices).where(RequestedServices.domain == domain).where(RequestedServices.uid==uid))
    request_service = db_result.first()

    if request_service is None:
        raise RequestNotFound()

    form_data_dict = form_data.model_dump()

    new_milestone = Milestones(**form_data_dict, request=request_service, requestUid=request_service.uid)
    session.add(new_milestone)
    await session.commit()
    await session.refresh(request_service)
    return request_service

@request_router.post(
    "/{uid}/milestones/{milestoneUid}",
    status_code=status.HTTP_200_OK,
    response_model=RequestedServicesRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": Message},
        status.HTTP_401_UNAUTHORIZED: {"model": Message},
        status.HTTP_404_NOT_FOUND: {"model": Message},
        status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: {"model": ConflictingIpMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": Message},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
    }
)
async def update_milestones_for_a_request(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique request uid")], milestoneUid: Annotated[uuid.UUID, Path(title="Unique milestone uid")], form_data: CreateOrUpdateMilestones, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(RequestedServices).where(RequestedServices.domain == domain).where(RequestedServices.uid==uid))
    request_service = db_result.first()

    if request_service is None:
        raise RequestNotFound()

    m_db_result = await session.exec(select(Milestones).where(Milestones.uid == milestoneUid).where(Milestones.requestUid == uid))
    milestone_to_update = m_db_result.first()

    if milestone_to_update is not None:
        raise MilestoneNotFound()

    form_data_dict = form_data.model_dump()

    for k, v in form_data_dict.items():
        # set new values if they are not none, has the keys "images" or "stacks" and the completed key value is not already what the existing project has
        if v is not None:
            setattr(milestone_to_update, k, v)

    await session.commit()
    await session.refresh(request_service)
    return request_service

