from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ResultBase(BaseModel):
    quantification_method_id: Optional[int] = None
    recovery_id: Optional[int] = None
    dna_concentration: Optional[float] = None
    degradation_category_id: Optional[int] = None
    inhibition_category_id: Optional[int] = None


class ResultCreate(ResultBase):
    pcrs: List["PCRCreate"] = []


class ResultUpdate(ResultBase):
    pcrs: Optional[List["PCRCreate"]] = None


class ResultRead(ResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantification_method: Optional["QuantificationMethodRead"] = None
    recovery: Optional["RecoveryRead"] = None
    degradation_category: Optional["DegradationCategoryRead"] = None
    inhibition_category: Optional["InhibitionCategoryRead"] = None
    pcrs: List["PCRRead"] = []


from app.schemas.degradation_category import DegradationCategoryRead
from app.schemas.inhibition_category import InhibitionCategoryRead
from app.schemas.quantification_method import QuantificationMethodRead
from app.schemas.recovery import RecoveryRead
from app.schemas.pcr import PCRCreate, PCRRead
