from typing import Optional

from pydantic import BaseModel, ConfigDict


class StudyBase(BaseModel):
    laboratory_id: Optional[int] = None
    doi: Optional[str] = None
    authors: Optional[str] = None
    description: Optional[str] = None
    year: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    journal: Optional[str] = None
    plan_a_transfer_experiment: Optional[bool] = None
    add_data_to_repository: Optional[bool] = None
    quality_check_passed: Optional[bool] = None
    corresponding_author_contact: Optional[str] = None


class StudyCreate(StudyBase):
    pass


class StudyUpdate(StudyBase):
    pass


class StudyRead(StudyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
