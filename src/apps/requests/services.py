from decimal import Decimal
import random
from fastapi import UploadFile
from src.apps.requests.models import ServiceFeatures
from src.db.cloudinary import upload_image
from sqlmodel.ext.asyncio.session import AsyncSession


async def createFeatureImageUrl(new_feature: ServiceFeatures, image: UploadFile, session: AsyncSession):
    image_url = await upload_image(image)
    new_feature.image = image_url
    session.add(new_feature)
    session.commit()


def get_random_decimal(start: Decimal, end: Decimal) -> Decimal:
    # Convert the decimal values to floats
    start_float = float(start)
    end_float = float(end)

    # Generate a random float between the two values
    random_float = random.uniform(start_float, end_float)

    # Convert the float back to a decimal
    return Decimal(str(random_float))
