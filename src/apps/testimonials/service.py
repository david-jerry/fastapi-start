from fastapi import UploadFile
from src.apps.testimonials.models import Testimonial
from src.db.cloudinary import upload_image
from sqlmodel.ext.asyncio.session import AsyncSession


async def createImageUrl(testimonial: Testimonial, image: UploadFile, session: AsyncSession):
    image_url = await upload_image(image)
    testimonial.image = image_url
    session.commit()
    await session.refresh(testimonial)

