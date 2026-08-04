from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClassificationCriteriaBase(BaseModel):
    name: Optional[str] = None


class ClassificationCriteriaCreate(ClassificationCriteriaBase):
    pass


class ClassificationCriteriaUpdate(ClassificationCriteriaBase):
    pass


class ClassificationCriteriaRead(ClassificationCriteriaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
