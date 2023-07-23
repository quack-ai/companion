# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from fastapi import APIRouter

from app.api.api_v1.endpoints import guidelines, login, repos, users

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["access"])
api_router.include_router(repos.router, prefix="/repos", tags=["repos"])
api_router.include_router(guidelines.router, prefix="/guidelines", tags=["guidelines"])
