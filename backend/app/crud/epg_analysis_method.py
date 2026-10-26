from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.epg_analysis_method import EPGAnalysisMethod
from app.models.epg_analysis_method_dye_channel_threshold import (
    EPGAnalysisMethodDyeChannelThreshold,
)
from app.models.user import User
from app.schemas.epg_analysis_method import EPGAnalysisMethodCreate, EPGAnalysisMethodUpdate


class CRUDEPGAnalysisMethod(CRUDBase[EPGAnalysisMethod, EPGAnalysisMethodCreate, EPGAnalysisMethodUpdate]):
    def __init__(self):
        super().__init__(EPGAnalysisMethod)

    def _build_thresholds(
        self, thresholds
    ) -> list[EPGAnalysisMethodDyeChannelThreshold]:
        return [
            EPGAnalysisMethodDyeChannelThreshold(
                dye_channel_id=threshold.dye_channel_id,
                analytical_threshold=threshold.analytical_threshold,
                position=index,
            )
            for index, threshold in enumerate(thresholds)
        ]

    async def create(
        self, db: AsyncSession, obj_in: EPGAnalysisMethodCreate, user: Optional[User] = None
    ) -> EPGAnalysisMethod:
        obj_data = obj_in.model_dump(
            exclude_none=True, exclude_unset=True, exclude={"dye_channel_thresholds"}
        )
        new_instance = self.model(**obj_data)
        new_instance.dye_channel_thresholds = self._build_thresholds(
            obj_in.dye_channel_thresholds
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
        obj_in: EPGAnalysisMethodUpdate,
        exclude: dict = {},
        exclude_none: bool = True,
        exclude_unset: bool = True,
        user: Optional[User] = None,
    ) -> EPGAnalysisMethod:
        instance = await self.get(db, id)

        update_data = obj_in.model_dump(
            exclude={*exclude, "dye_channel_thresholds"},
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )
        for field, value in update_data.items():
            setattr(instance, field, value)

        # The nested list is replaced wholesale on every save - the form
        # always submits the full set of rows, there's no partial edit.
        if obj_in.dye_channel_thresholds is not None:
            instance.dye_channel_thresholds = self._build_thresholds(
                obj_in.dye_channel_thresholds
            )

        try:
            await db.commit()
            await db.refresh(instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return instance


crud_epg_analysis_method = CRUDEPGAnalysisMethod()
