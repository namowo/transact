from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    donor_surface_id: Optional[int] = None
    recipient_surface_id: Optional[int] = None
    duration: Optional[str] = None
    pressure: Optional[str] = None
    friction_applied: Optional[str] = None
    contact_area: Optional[str] = None
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
