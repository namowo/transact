from typing import Optional

from pydantic import BaseModel, ConfigDict


class PickingMethodBase(BaseModel):
    scraping_device: Optional[str] = None
    description: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None
    supplier: Optional[str] = None


class PickingMethodCreate(PickingMethodBase):
    pass


class PickingMethodUpdate(PickingMethodBase):
    pass


class PickingMethodRead(PickingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
