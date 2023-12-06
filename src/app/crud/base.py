# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import Any, Generic, List, Tuple, Type, TypeVar, Union, cast

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import exc
from sqlmodel import SQLModel, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

__all__ = ["BaseCRUD"]


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]) -> None:
        self.session = session
        self.model = model

    async def create(self, payload: CreateSchemaType) -> ModelType:
        entry = self.model(**payload.dict())
        try:
            self.session.add(entry)
            await self.session.commit()
        except exc.IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An entry with the same index already exists.",
            )
        await self.session.refresh(entry)

        return entry

    async def get(self, entry_id: int, strict: bool = False) -> Union[ModelType, None]:
        entry = await self.session.get(self.model, entry_id)
        if strict and entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {self.model.__name__} has no corresponding entry.",
            )
        return entry

    async def get_by(self, field_name: str, val: Union[str, int], strict: bool = False) -> Union[ModelType, None]:
        statement = select(self.model).where(getattr(self.model, field_name) == val)
        results = await self.session.execute(statement=statement)
        entry = results.scalar_one_or_none()
        if strict and entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {self.model.__name__} has no corresponding entry.",
            )
        return entry

    async def fetch_all(self, filter_pair: Union[Tuple[str, Any], None] = None) -> List[ModelType]:
        statement = select(self.model)
        if isinstance(filter_pair, tuple):
            statement = statement.where(getattr(self.model, filter_pair[0]) == filter_pair[1])
        results = await self.session.execute(statement=statement)
        return results.scalars()  # type: ignore[return-value]

    async def update(self, entry_id: int, payload: UpdateSchemaType) -> ModelType:
        access = cast(ModelType, await self.get(entry_id, strict=True))
        values = payload.dict(exclude_unset=True)

        for k, v in values.items():
            setattr(access, k, v)

        self.session.add(access)
        await self.session.commit()
        await self.session.refresh(access)

        return access

    async def delete(self, entry_id: int) -> None:
        await self.get(entry_id, strict=True)
        statement = delete(self.model).where(self.model.id == entry_id)  # type: ignore[attr-defined]

        await self.session.execute(statement=statement)
        await self.session.commit()
