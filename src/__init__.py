from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi.responses import JSONResponse
from pydantic_core import ValidationError

from src.apps.accounts.dependencies import get_ip_address
from src.db.db import init_db
from src.utils.logger import LOGGER
from src.errors import register_all_errors, BannedIp, InsufficientPermission, InvalidCredentials, ProxyConflict, UnknownIpConflict, UserAlreadyExists, UserBlocked, UserNotFound
from src.middleware import register_middleware
from src.config.settings import Config

from src.apps.accounts.views import auth_router, user_router
from src.apps.faqs.views import faq_router
from src.apps.testimonials.views import testimonial_router
from src.apps.analytics.views import analysis_router
from src.apps.projects.views import project_router
from src.apps.requests.views import service_router, request_router

from fastapi import FastAPI, Request
from fastapi_pagination import add_pagination
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi import status
from fastapi.encoders import jsonable_encoder

version = Config.VERSION

description = f"""
## Fullstack Developer API

### Overview

This is the official API Documentation on how to use features relating to a fullstack developer portfolio

### Base URL

```
https://api.jeremiahedavid.online/{version}
```

### Authentication

There are two methods for authentication:

* **OAuth 2.0:** Use OAuth 2.0 for secure authentication and authorization.
* **API Key:** Alternatively, you can use an API key for authentication. Contact Next Stocks support to obtain an API key.

### Endpoints

[COMING SOON]

### Request/Response Format

* **Request:** JSON
* **Response:** JSON

### Error Handling

* **HTTP Status Codes:** The API will return appropriate HTTP status codes (e.g., 200 for success, 400 for bad requests, 500 for server errors).
* **Error Messages:** Error messages will be provided in the JSON response body.

### Rate Limiting
* **None
The API may have rate limits to prevent abuse. Please refer to the official Next Stocks API documentation for specific rate limits.

### Additional Notes

* For detailed documentation, including request parameters, response structures, and example usage, please refer to the official [API Documentation](https://api.jeremiahedavid.online/{version}/docs).
* The API may be subject to changes, so it's recommended to check the documentation regularly for updates.
    """

version_prefix = f"/{version}"


@asynccontextmanager
async def life_span(app: FastAPI):
    LOGGER.info("Server is running")
    await init_db()
    yield
    LOGGER.info("Server has stopped")


app = FastAPI(
    title="Jeremiah David API - #A Fullstack Developer Endpoint",
    description=description,
    version=version,
    lifespan=life_span,
    license_info={
        "name": "MIT License",
        "url": "https://github.com/david-jerry/portfolio-api/blob/main/LICENSE",
    },
    contact={
        "name": "Jeremiah David",
        "url": "https://github.com/david-jerry",
        "email": "jeremiahedavid@gmail.com",
    },
    terms_of_service="https://github.com/david-jerry/portfolio-api/blob/main/TERMS.md",
    openapi_url=f"{version_prefix}/openapi.json",
    docs_url=f"{version_prefix}",
    redoc_url=f"{version_prefix}/docs",
)

register_all_errors(app)

register_middleware(app)

add_pagination(app)

app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["auth"])
app.include_router(user_router, prefix=f"{version_prefix}/users", tags=["users"])
app.include_router(faq_router, prefix=f"{version_prefix}/faqs", tags=["faqs"])
app.include_router(testimonial_router, prefix=f"{version_prefix}/testimonials", tags=["testimonials"])
app.include_router(project_router, prefix=f"{version_prefix}/projects", tags=["projects"])
app.include_router(analysis_router, prefix=f"{version_prefix}/analytics", tags=["analytics"])
app.include_router(service_router, prefix=f"{version_prefix}/services", tags=["services"])
app.include_router(request_router, prefix=f"{version_prefix}/job-requests", tags=["job-requests"])
