from datetime import datetime, timedelta
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Form, Path, Request, UploadFile, status
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
from src.db.cloudinary import upload_image
from src.db.db import get_session
from src.apps.accounts.services import UserService
from src.config.settings import Config
from src.errors import FAQNotFound, InsufficientPermission, ProjectNotFound
from src.utils.logger import LOGGER

session = Annotated[AsyncSession, Depends(get_session)]
user_service = UserService()
project_router = APIRouter()


@project_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
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
async def add_new_projects(
    request: Request,
    background_tasks: BackgroundTasks,
    formData: CreateOrUpdateProjects,  # File upload for images
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    # Process the stacks data
    all_stacks: List[ProjectStacks] = []  # list of stacks

    # Split the stacks string by comma to get individual stack names
    stack_list = [stack.strip() for stack in formData.stacks.split(',')]

    # Process the stacks data
    for stack in stack_list:
        db_result = await session.exec(select(ProjectStacks).where(ProjectStacks.name == stack))
        stack_exist: Optional[ProjectStacks] = await db_result.first()

        if stack_exist is None:
            new_stack = ProjectStacks(name=stack)
            session.add(new_stack)
            all_stacks.append(new_stack)
        else:
            all_stacks.append(stack_exist)

    new_project = Projects(
        name=formData.name,
        existingLink=formData.existingLink,
        description=formData.description,
        completed=formData.completed,
        domain=domain,
        stacks=all_stacks
    )

    # Link project to stacks
    for s in all_stacks:
        LOGGER.debug(s)
        new_link = ProjectStacksLink(stackUid=s.uid, projectUid=new_project.uid)
        session.add(new_link)

    # Handle images
    if len(formData.images) > 0:
        # only run when the images list has at least one item to add to the project
        for image in formData.images:
            background_tasks.add_task(createImageUrl, new_project, image, session)

    session.add(new_project)
    await session.commit()

    page = await paginate(session, select(Projects).where(Projects.domain == domain).order_by(Projects.name, Projects.createdAt))
    return page.model_dump()

@project_router.get(
    "",
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
async def get_all_projects(request: Request, session: AsyncSession = Depends(get_session)):
    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"
    page = await paginate(session, select(Projects).where(Projects.domain==domain).order_by(Projects.name, Projects.createdAt))
    return page.model_dump()

@project_router.patch(
    "/{uid}",
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
async def update_project(request: Request, background_tasks: BackgroundTasks, uid: Annotated[uuid.UUID, Path(title="Unique project uid")], form_data: UpdateProjects, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Projects).where(Projects.domain == domain).where(Projects.uid==uid))
    project_to_update = db_result.first()

    if project_to_update is None:
        raise ProjectNotFound()

    form_data_dict = form_data.model_dump()

    if len(form_data.images) > 0:
        # only run when the images list has atleast one item to add to the project
        for image in form_data.images:
            background_tasks.add_task(createImageUrl, project_to_update, image, session)

    # Process the stacks data
    all_stacks: List[ProjectStacks] = []  # list of stacks

    # Split the stacks string by comma to get individual stack names
    stack_list = [stack.strip() for stack in form_data.stacks.split(',')]

    # Process the stacks data

    if len(form_data.stacks) > 0:
        for stack in stack_list:
            # determine if the stack first exists ie: it has been created
            db_result = await session.exec(select(ProjectStacks).where(ProjectStacks.name == stack))
            stack_exist: Optional[ProjectStacks] = await db_result.first()

            if stack_exist is None:
                # if the stack does not exist, create it and add to the existing project
                new_stack = ProjectStacks(name=stack)
                stack_link = ProjectStacksLink(stackUid=new_stack.uid, projectUid=project_to_update.uid)
                session.add(stack_link)
                session.add(new_stack)
                project_to_update.stacks.append(new_stack)
            else:
                # if the stack exist, check if it is assigned already to the existing project else remove it
                project_db_result = await session.exec(select(Projects).where(Projects.uid==project_to_update.uid).where(stack_exist in Projects.stacks))
                project_exists = project_db_result.first()
                if project_exists is not None:
                    project_to_update.stacks.remove(stack_exist)
                    await session.refresh(project_to_update)
                else:
                    project_to_update.stacks.append(stack_exist)


    for k, v in form_data_dict.items():
        # set new values if they are not none, has the keys "images" or "stacks" and the completed key value is not already what the existing project has
        if (k != "images" or k != "stacks") and v is not None:
            if k == "completed" and v != project_to_update.completed:
                setattr(project_to_update, k, v)
            else:
                setattr(project_to_update, k, v)

    await session.commit()
    await session.refresh(project_to_update)

    page = await paginate(session, select(Projects).where(Projects.domain==domain).order_by(Projects.name, Projects.createdAt))
    return page.model_dump()

@project_router.delete(
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
async def delete_project(request: Request, uid: Annotated[uuid.UUID, Path(title="Unique project uid")], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not user.isCompany:
        raise InsufficientPermission()

    domain = request.headers.get("domain")
    if domain is None:
        domain = "https://jeremiahedavid.online"

    db_result = await session.exec(select(Projects).where(Projects.domain == domain).where(Projects.uid==uid))
    project_to_delete = db_result.first()

    await session.delete(project_to_delete)
    await session.commit()

    return {
        "message": f"{project_to_delete.name} has been deleted successfully"
    }

