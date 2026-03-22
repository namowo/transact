from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConditionDuringContactBase(BaseModel):
    temperature: Optional[str] = None
    humidity: Optional[str] = None
    uv_irradiation: Optional[str] = None
    indoors: Optional[bool] = None
    change_over_time: Optional[str] = None
    duration_of_disturbance: Optional[int] = None
    description_of_disturbance: Optional[str] = None
    disturbance_category_id: Optional[int] = None
    geographic_location_category_id: Optional[int] = None


class ConditionDuringContactCreate(ConditionDuringContactBase):
    pass


class ConditionDuringContactUpdate(ConditionDuringContactBase):
    pass


class ConditionDuringContactRead(ConditionDuringContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    disturbance_category: Optional["DisturbanceCategoryRead"] = None
    geographic_location_category: Optional["GeographicLocationCategoryRead"] = None


from app.schemas.disturbance_category import DisturbanceCategoryRead
from app.schemas.geographic_location_category import GeographicLocationCategoryRead
