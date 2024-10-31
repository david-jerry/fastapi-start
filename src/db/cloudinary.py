import cloudinary
from cloudinary.uploader import upload # type: ignore
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import JSONResponse
from src.config.settings import Config

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_KEY,
    api_secret=Config.CLOUDINARY_SECRET,
)

async def upload_image(image: UploadFile):
    try:
        upload_result = upload(image.file)
        file_url = upload_result["secure_url"]
        return file_url
    except Exception as e:
        raise JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f"Error uploading images: {e}"
        )
