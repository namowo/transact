from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SecondsTimedelta


class ContactBase(BaseModel):
    contact_template_id: Optional[int] = None
    donor_surface_id: Optional[int] = None
    recipient_surface_id: Optional[int] = None
    duration: Optional[SecondsTimedelta] = None
    pressure: Optional[float] = None
    pressure_estimate_id: Optional[int] = None
    friction_applied: Optional[float] = None
    friction_applied_estimate_id: Optional[int] = None
    contact_area: Optional[float] = None
    description_of_contact: Optional[str] = None
    activity_category_id: Optional[int] = None
    condition_during_contact_id: Optional[int] = None


class ContactCreate(ContactBase):
    contact_template_id: int


class ContactUpdate(ContactBase):
    pass


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donor_surface: Optional["SurfaceRead"] = None
    recipient_surface: Optional["SurfaceRead"] = None
    pressure_estimate: Optional["PressureEstimateRead"] = None
    friction_applied_estimate: Optional["FrictionAppliedEstimateRead"] = None
    activity_category: Optional["ActivityCategoryRead"] = None
    condition_during_contact: Optional["ConditionDuringContactRead"] = None


from app.schemas.surface import SurfaceRead
from app.schemas.pressure_estimate import PressureEstimateRead
from app.schemas.friction_applied_estimate import FrictionAppliedEstimateRead
from app.schemas.activity_category import ActivityCategoryRead
from app.schemas.condition_during_contact import ConditionDuringContactRead
