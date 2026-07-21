from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.author import Author
from app.models.study import Study
from app.models.user import User
from app.schemas.study import StudyCreate, StudyUpdate


def _authors_from(authors) -> list[Author]:
    return [
        Author(**author.model_dump(), position=index)
        for index, author in enumerate(authors)
    ]


class CRUDStudy(CRUDBase[Study, StudyCreate, StudyUpdate]):
    def __init__(self):
        super().__init__(Study)

    async def create(self, db: AsyncSession, obj_in: StudyCreate) -> Study:
        obj_data = obj_in.model_dump(
            exclude={"authors"}, exclude_none=True, exclude_unset=True
        )
        new_study = Study(**obj_data)
        new_study.authors = _authors_from(obj_in.authors)
        db.add(new_study)

        try:
            await db.commit()
            await db.refresh(new_study)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return new_study

    async def update(self, db: AsyncSession, id: int, obj_in: StudyUpdate) -> Study:
        study = await self.get(db, id)
        update_data = obj_in.model_dump(
            exclude={"authors"}, exclude_none=True, exclude_unset=True
        )
        for field, value in update_data.items():
            setattr(study, field, value)

        if obj_in.authors is not None:
            study.authors = _authors_from(obj_in.authors)

        try:
            await db.commit()
            await db.refresh(study)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return study

    async def pass_quality_check(
        self, db: AsyncSession, study: Study, reviewer: User
    ) -> Study:
        study.quality_check_passed = True
        study.published = True
        study.quality_checked_by_id = reviewer.id
        study.quality_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            await db.commit()
            await db.refresh(study)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return study


crud_study = CRUDStudy()
