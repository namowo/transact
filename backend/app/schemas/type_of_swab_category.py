from typing import Optional

from pydantic import BaseModel, ConfigDict


class TypeOfSwabCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None


class TypeOfSwabCategoryCreate(TypeOfSwabCategoryBase):
    pass


class TypeOfSwabCategoryUpdate(TypeOfSwabCategoryBase):
    pass


class TypeOfSwabCategoryRead(TypeOfSwabCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier: Optional["SupplierRead"] = None


from app.schemas.supplier import SupplierRead
