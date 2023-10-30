# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from fastapi import APIRouter

from app.api.api_v1.endpoints import compute, guidelines, login, repos, users

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["access"])
api_router.include_router(repos.router, prefix="/repos", tags=["repos"])
api_router.include_router(guidelines.router, prefix="/guidelines", tags=["guidelines"])
api_router.include_router(compute.router, prefix="/compute", tags=["compute"])
