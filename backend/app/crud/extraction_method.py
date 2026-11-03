from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.extraction_method import ExtractionMethod
from app.models.extraction_method_lysis_buffer_component import (
    ExtractionMethodLysisBufferComponent,
)
from app.models.user import User
from app.schemas.extraction_method import ExtractionMethodCreate, ExtractionMethodUpdate


class CRUDExtractionMethod(CRUDBase[ExtractionMethod, ExtractionMethodCreate, ExtractionMethodUpdate]):
    def __init__(self):
        super().__init__(ExtractionMethod)

    def _build_components(
        self, components
    ) -> list[ExtractionMethodLysisBufferComponent]:
        return [
            ExtractionMethodLysisBufferComponent(
                lysis_buffer_component_id=component.lysis_buffer_component_id,
                volume=component.volume,
                position=index,
            )
            for index, component in enumerate(components)
        ]

    async def create(
        self, db: AsyncSession, obj_in: ExtractionMethodCreate, user: Optional[User] = None
    ) -> ExtractionMethod:
        obj_data = obj_in.model_dump(
            exclude_none=True, exclude_unset=True, exclude={"lysis_buffer_components"}
        )
        new_instance = self.model(**obj_data)
        new_instance.lysis_buffer_components = self._build_components(
            obj_in.lysis_buffer_components
        )
        db.add(new_instance)

        try:
            await db.commit()
            await db.refresh(new_instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return new_instance

    async def update(
        self,
        db: AsyncSession,
        id,
        obj_in: ExtractionMethodUpdate,
        exclude: dict = {},
        exclude_none: bool = True,
        exclude_unset: bool = True,
        user: Optional[User] = None,
    ) -> ExtractionMethod:
        instance = await self.get(db, id)

        update_data = obj_in.model_dump(
            exclude={*exclude, "lysis_buffer_components"},
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )
        for field, value in update_data.items():
            setattr(instance, field, value)

        # The nested list is replaced wholesale on every save - the form
        # always submits the full set of rows, there's no partial edit.
        if obj_in.lysis_buffer_components is not None:
            instance.lysis_buffer_components = self._build_components(
                obj_in.lysis_buffer_components
            )

        try:
            await db.commit()
            await db.refresh(instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return instance


crud_extraction_method = CRUDExtractionMethod()
