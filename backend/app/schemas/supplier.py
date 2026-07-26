from typing import Optional

from pydantic import BaseModel, ConfigDict


class SupplierBase(BaseModel):
    name: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
