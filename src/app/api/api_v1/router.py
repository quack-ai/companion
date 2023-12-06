# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from fastapi import APIRouter

from app.api.api_v1.endpoints import compute, guidelines, login, repos, users

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(repos.router, prefix="/repos", tags=["repos"])
api_router.include_router(guidelines.router, prefix="/guidelines", tags=["guidelines"])
api_router.include_router(compute.router, prefix="/compute", tags=["compute"])
