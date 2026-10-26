from typing import List, Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.schemas.common import SecondsTimedelta
from app.schemas.extraction_method_lysis_buffer_component import (
    ExtractionMethodLysisBufferComponentCreate,
    ExtractionMethodLysisBufferComponentRead,
)


class ExtractionMethodBase(BaseModel):
    laboratory_id: Optional[UUID] = None
    principle_of_extraction_method_category_id: Optional[UUID] = None
    extraction_protocol: Optional[str] = None
    extraction_platform_id: Optional[UUID] = None
    lysis_incubation_time: Optional[SecondsTimedelta] = None
    lysis_incubation_temperature: Optional[int] = None
    thermoshaker_id: Optional[UUID] = None
    rcf: Optional[int] = None
    volume_of_lysate_used_for_extraction: Optional[int] = None
    application_of_further_purification_step: Optional[bool] = None
    description_of_further_purification_step: Optional[str] = None
    abbreviations_to_manufacturers_protocol: Optional[str] = None


class ExtractionMethodCreate(ExtractionMethodBase):
    lysis_buffer_components: List[ExtractionMethodLysisBufferComponentCreate] = []


class ExtractionMethodUpdate(ExtractionMethodBase):
    lysis_buffer_components: Optional[List[ExtractionMethodLysisBufferComponentCreate]] = None


class ExtractionMethodRead(ExtractionMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    laboratory: Optional["LaboratoryRead"] = None
    principle_of_extraction_method_category: Optional["PrincipleOfExtractionMethodCategoryRead"] = None
    extraction_platform: Optional["PlatformRead"] = None
    thermoshaker: Optional["ThermoshakerRead"] = None
    lysis_buffer_components: List[ExtractionMethodLysisBufferComponentRead] = []


from app.schemas.laboratory import LaboratoryRead
from app.schemas.principle_of_extraction_method_category import PrincipleOfExtractionMethodCategoryRead
from app.schemas.platform import PlatformRead
from app.schemas.thermoshaker import ThermoshakerRead
