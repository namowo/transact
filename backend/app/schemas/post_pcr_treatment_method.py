from typing import Optional

from pydantic import BaseModel, ConfigDict


class PostPCRTreatmentMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    application_of_post_pcr_purification_step: Optional[bool] = None
    description_of_post_pcr_purification_step: Optional[str] = None
    dilution_of_pcr_product: Optional[str] = None
    dilution_factor: Optional[int] = None


class PostPCRTreatmentMethodCreate(PostPCRTreatmentMethodBase):
    pass


class PostPCRTreatmentMethodUpdate(PostPCRTreatmentMethodBase):
    pass


class PostPCRTreatmentMethodRead(PostPCRTreatmentMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
