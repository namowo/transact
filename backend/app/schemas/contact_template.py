from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SecondsTimedelta


class ContactTemplateBase(BaseModel):
    donor_surface_template_id: Optional[int] = None
    recipient_surface_template_id: Optional[int] = None
    duration: Optional[SecondsTimedelta] = None
    pressure_estimate_id: Optional[int] = None
    friction_applied_estimate_id: Optional[int] = None
    contact_area: Optional[float] = None
    description_of_contact: Optional[str] = None
    activity_category_id: Optional[int] = None
    condition_during_contact_id: Optional[int] = None


class ContactTemplateCreate(ContactTemplateBase):
    scenario_ids: list[int] = []


class ContactTemplateUpdate(ContactTemplateBase):
    scenario_ids: Optional[list[int]] = None


class ContactTemplateRead(ContactTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donor_surface_template: Optional["SurfaceTemplateRead"] = None
    recipient_surface_template: Optional["SurfaceTemplateRead"] = None
    pressure_estimate: Optional["PressureEstimateRead"] = None
    friction_applied_estimate: Optional["FrictionAppliedEstimateRead"] = None
    activity_category: Optional["ActivityCategoryRead"] = None
    condition_during_contact: Optional["ConditionDuringContactRead"] = None
    contacts: list["ContactRead"] = []


from app.schemas.surface_template import SurfaceTemplateRead
from app.schemas.pressure_estimate import PressureEstimateRead
from app.schemas.friction_applied_estimate import FrictionAppliedEstimateRead
from app.schemas.activity_category import ActivityCategoryRead
from app.schemas.condition_during_contact import ConditionDuringContactRead
from app.schemas.contact import ContactRead
