from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class QuantificationMethodBase(BaseModel):
    laboratory_id: Optional[UUID] = None
    principle_of_quant_method_category_id: Optional[UUID] = None
    kit_id: Optional[UUID] = None
    manufacturer_id: Optional[UUID] = None
    platform_id: Optional[UUID] = None
    description_of_protocol: Optional[str] = None
    abbreviations_to_manufacturers_protocol: Optional[str] = None


class QuantificationMethodCreate(QuantificationMethodBase):
    pass


class QuantificationMethodUpdate(QuantificationMethodBase):
    pass


class QuantificationMethodRead(QuantificationMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    laboratory: Optional["LaboratoryRead"] = None
    principle_of_quant_method_category: Optional["PrincipleOfQuantMethodCategoryRead"] = None
    kit: Optional["QuantificationKitRead"] = None
    manufacturer: Optional["ManufacturerRead"] = None
    platform: Optional["PlatformRead"] = None


from app.schemas.laboratory import LaboratoryRead
from app.schemas.principle_of_quant_method_category import PrincipleOfQuantMethodCategoryRead
from app.schemas.quantification_kit import QuantificationKitRead
from app.schemas.manufacturer import ManufacturerRead
from app.schemas.platform import PlatformRead
