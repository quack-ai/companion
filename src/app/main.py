# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
import time

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.api.api_v1.router import api_router
from app.core.config import settings
from app.db import init_db

logger = logging.getLogger("uvicorn.error")

# Sentry
if isinstance(settings.SENTRY_DSN, str):
    sentry_sdk.init(
        settings.SENTRY_DSN,
        release=settings.VERSION,
        server_name=settings.SERVER_NAME,
        environment="production" if isinstance(settings.SERVER_NAME, str) else None,
        traces_sample_rate=0.0,
    )
    logger.info(f"Sentry middleware enabled on server {settings.SERVER_NAME}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    debug=settings.DEBUG,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Database connection
@app.on_event("startup")
async def startup() -> None:
    await init_db()


# Routing
app.include_router(api_router, prefix=settings.API_V1_STR)


# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if isinstance(settings.SENTRY_DSN, str):
    app.add_middleware(SentryAsgiMiddleware)


# Docs
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": settings.LOGO_URL}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]
