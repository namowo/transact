from typing import Optional
from datetime import timedelta

from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    scenario_id: Optional[int] = None
    donor_surface_id: Optional[int] = None
    recipient_surface_id: Optional[int] = None
    duration: Optional[timedelta] = None
    pressure: Optional[float] = None
    friction_applied: Optional[float] = None
    contact_area: Optional[float] = None
    description_of_contact: Optional[str] = None
    activity_category_id: Optional[int] = None
    condition_during_contact_id: Optional[int] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donor_surface: Optional["SurfaceRead"] = None
    recipient_surface: Optional["SurfaceRead"] = None
    activity_category: Optional["ActivityCategoryRead"] = None
    condition_during_contact: Optional["ConditionDuringContactRead"] = None


from app.schemas.surface import SurfaceRead
from app.schemas.activity_category import ActivityCategoryRead
from app.schemas.condition_during_contact import ConditionDuringContactRead
