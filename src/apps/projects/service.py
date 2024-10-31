from fastapi import UploadFile
from src.apps.projects.models import ProjectImages, Projects
from src.db.cloudinary import upload_image
from sqlmodel.ext.asyncio.session import AsyncSession


async def createImageUrl(new_project: Projects, image: UploadFile, session: AsyncSession):
    image_url = await upload_image(image)
    new_image = ProjectImages(image=image_url, project=new_project, projectUid=new_project.uid)
    session.add(new_image)
    session.commit()

