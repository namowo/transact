from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PostPCRTreatmentMethodBase(BaseModel):
    laboratory_id: Optional[UUID] = None
    application_of_post_pcr_purification_step: Optional[bool] = None
    description_of_post_pcr_purification_step: Optional[str] = None
    dilution_of_pcr_product: Optional[bool] = None
    dilution_factor: Optional[float] = None


class PostPCRTreatmentMethodCreate(PostPCRTreatmentMethodBase):
    pass


class PostPCRTreatmentMethodUpdate(PostPCRTreatmentMethodBase):
    pass


class PostPCRTreatmentMethodRead(PostPCRTreatmentMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
