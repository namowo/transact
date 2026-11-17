from typing import List, Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict, computed_field


class ResultBase(BaseModel):
    quantification_method_id: Optional[UUID] = None
    sample_id: Optional[UUID] = None
    dna_concentration: Optional[float] = None
    degradation_category_id: Optional[UUID] = None
    inhibition_category_id: Optional[UUID] = None


class ResultCreate(ResultBase):
    pcrs: List["PCRCreate"] = []


class ResultUpdate(ResultBase):
    pcrs: Optional[List["PCRCreate"]] = None


class ResultRead(ResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quantification_method: Optional["QuantificationMethodRead"] = None
    sample: Optional["SampleRead"] = None
    degradation_category: Optional["DegradationCategoryRead"] = None
    inhibition_category: Optional["InhibitionCategoryRead"] = None
    pcrs: List["PCRRead"] = []

    @computed_field
    @property
    def dna_quantity(self) -> Optional[float]:
        elution_volume = self.sample.elution_volume if self.sample else None
        if self.dna_concentration is None or elution_volume is None:
            return None
        return self.dna_concentration * elution_volume


from app.schemas.degradation_category import DegradationCategoryRead
from app.schemas.inhibition_category import InhibitionCategoryRead
from app.schemas.quantification_method import QuantificationMethodRead
from app.schemas.sample import SampleRead
from app.schemas.pcr import PCRCreate, PCRRead
