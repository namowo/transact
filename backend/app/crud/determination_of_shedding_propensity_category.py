from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.author import get_or_create_author
from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.determination_of_shedding_propensity_category import (
    DeterminationOfSheddingPropensityCategory,
)
from app.models.determination_of_shedding_propensity_category_restriction import (
    DeterminationOfSheddingPropensityCategoryRestriction,
)
from app.models.determination_of_shedding_propensity_category_shedder_test import (
    DeterminationOfSheddingPropensityCategoryShedderTest,
)
from app.models.monitored_transfer_factor import MonitoredTransferFactor
from app.schemas.determination_of_shedding_propensity_category import (
    DeterminationOfSheddingPropensityCategoryCreate,
    DeterminationOfSheddingPropensityCategoryUpdate,
)

ASSOCIATION_FIELDS = {
    "authors",
    "restrictions",
    "monitored_transfer_factor_ids",
    "shedder_tests",
}


class CRUDDeterminationOfSheddingPropensityCategory(
    CRUDBase[
        DeterminationOfSheddingPropensityCategory,
        DeterminationOfSheddingPropensityCategoryCreate,
        DeterminationOfSheddingPropensityCategoryUpdate,
    ]
):
    def __init__(self):
        super().__init__(DeterminationOfSheddingPropensityCategory)

    async def _authors_from(self, db: AsyncSession, authors) -> list:
        return [await get_or_create_author(db, author_in) for author_in in authors]

    async def _restrictions_from(
        self, db: AsyncSession, restrictions
    ) -> list[DeterminationOfSheddingPropensityCategoryRestriction]:
        return [
            DeterminationOfSheddingPropensityCategoryRestriction(
                **restriction.model_dump()
            )
            for restriction in restrictions
        ]

    async def _shedder_tests_from(
        self, db: AsyncSession, shedder_tests
    ) -> list[DeterminationOfSheddingPropensityCategoryShedderTest]:
        return [
            DeterminationOfSheddingPropensityCategoryShedderTest(
                **shedder_test.model_dump()
            )
            for shedder_test in shedder_tests
        ]

    async def _monitored_transfer_factors_from(
        self, db: AsyncSession, ids: list[int]
    ) -> list[MonitoredTransferFactor]:
        if not ids:
            return []
        result = await db.execute(
            select(MonitoredTransferFactor).where(MonitoredTransferFactor.id.in_(ids))
        )
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, obj_in: DeterminationOfSheddingPropensityCategoryCreate
    ) -> DeterminationOfSheddingPropensityCategory:
        obj_data = obj_in.model_dump(
            exclude=ASSOCIATION_FIELDS, exclude_none=True, exclude_unset=True
        )
        new_instance = DeterminationOfSheddingPropensityCategory(**obj_data)
        new_instance.authors = await self._authors_from(db, obj_in.authors)
        new_instance.restrictions = await self._restrictions_from(
            db, obj_in.restrictions
        )
        new_instance.shedder_tests = await self._shedder_tests_from(
            db, obj_in.shedder_tests
        )
        new_instance.monitored_transfer_factors = (
            await self._monitored_transfer_factors_from(
                db, obj_in.monitored_transfer_factor_ids
            )
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
        id: int,
        obj_in: DeterminationOfSheddingPropensityCategoryUpdate,
    ) -> DeterminationOfSheddingPropensityCategory:
        instance = await self.get(db, id)
        update_data = obj_in.model_dump(
            exclude=ASSOCIATION_FIELDS, exclude_none=True, exclude_unset=True
        )
        for field, value in update_data.items():
            setattr(instance, field, value)

        if obj_in.authors is not None:
            instance.authors = await self._authors_from(db, obj_in.authors)
        if obj_in.restrictions is not None:
            instance.restrictions = await self._restrictions_from(
                db, obj_in.restrictions
            )
        if obj_in.shedder_tests is not None:
            instance.shedder_tests = await self._shedder_tests_from(
                db, obj_in.shedder_tests
            )
        if obj_in.monitored_transfer_factor_ids is not None:
            instance.monitored_transfer_factors = (
                await self._monitored_transfer_factors_from(
                    db, obj_in.monitored_transfer_factor_ids
                )
            )

        try:
            await db.commit()
            await db.refresh(instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return instance


crud_determination_of_shedding_propensity_category = (
    CRUDDeterminationOfSheddingPropensityCategory()
)
