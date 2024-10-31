from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging

from src.utils.logger import LOGGER

logger = logging.getLogger("uvicorn.access")
logger.disabled = True


def register_middleware(app: FastAPI):

    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        start_time = time.time()

        # Check if the request URL is the root "/"
        if request.url.path == "/":
            # Redirect to /api/v1/redocs
            return RedirectResponse(url="/v1")

        response = await call_next(request)
        processing_time = time.time() - start_time

        host = request.client.host
        port = request.client.port
        method = request.method
        path = request.url.path

        message = f"""
{host}:{port} - {method} - {path} - {response.status_code} completed after {processing_time}s
        """

        LOGGER.info(message)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "jeremiahedavid.online",
            "jeremiahedavid.com.ng",
        ],
    )
