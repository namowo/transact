from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExtractionMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    principle_of_extraction_method_category_id: Optional[int] = None
    extraction_protocol: Optional[str] = None
    extraction_platform: Optional[str] = None
    additional_lysis_buffer_components: Optional[str] = None
    volume_lysis_buffer_components: Optional[int] = None
    lysis_incubation_time: Optional[int] = None
    lysis_incubation_temperature: Optional[int] = None
    volume_of_lysate_used_for_extraction: Optional[int] = None
    application_of_further_purification_step: Optional[bool] = None
    description_of_further_purification_step: Optional[str] = None


class ExtractionMethodCreate(ExtractionMethodBase):
    pass


class ExtractionMethodUpdate(ExtractionMethodBase):
    pass


class ExtractionMethodRead(ExtractionMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None
    principle_of_extraction_method_category: Optional["PrincipleOfExtractionMethodCategoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
from app.schemas.principle_of_extraction_method_category import PrincipleOfExtractionMethodCategoryRead
