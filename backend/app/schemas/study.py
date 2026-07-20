from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class StudyBase(BaseModel):
    laboratory_id: Optional[int] = None
    doi: Optional[str] = None
    description: Optional[str] = None
    year: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    journal: Optional[str] = None
    plan_a_transfer_experiment: Optional[bool] = None
    add_data_to_repository: Optional[bool] = None
    quality_check_passed: Optional[bool] = None
    published: Optional[bool] = None
    corresponding_author_name: Optional[str] = None
    corresponding_author_email: Optional[str] = None
    corresponding_author_phone: Optional[str] = None


class StudyCreate(StudyBase):
    laboratory_id: int
    title: str
    authors: List["AuthorCreate"] = []

    @model_validator(mode="after")
    def _check_purpose_is_exclusive(self):
        if self.plan_a_transfer_experiment and self.add_data_to_repository:
            raise ValueError(
                "A study can either plan a transfer experiment or add data to the "
                "repository, not both."
            )
        return self


class StudyUpdate(StudyBase):
    authors: Optional[List["AuthorCreate"]] = None


class StudyRead(StudyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None
    authors: List["AuthorRead"] = []


from app.schemas.author import AuthorCreate, AuthorRead
from app.schemas.laboratory import LaboratoryRead
