from typing import Optional

from pydantic import BaseModel, ConfigDict


class QuantificationMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    principle_of_quant_method_category_id: Optional[int] = None
    kit: Optional[str] = None
    manufacturer: Optional[str] = None
    platform: Optional[str] = None
    description_of_protocol: Optional[str] = None
    abbreviations_to_manufacturers_protocol: Optional[str] = None


class QuantificationMethodCreate(QuantificationMethodBase):
    pass


class QuantificationMethodUpdate(QuantificationMethodBase):
    pass


class QuantificationMethodRead(QuantificationMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None
    principle_of_quant_method_category: Optional["PrincipleOfQuantMethodCategoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
from app.schemas.principle_of_quant_method_category import PrincipleOfQuantMethodCategoryRead
