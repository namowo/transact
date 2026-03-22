from typing import Optional

from pydantic import BaseModel, ConfigDict


class TypeOfSwabCategoryBase(BaseModel):
    type_of_swab_category: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None
    description: Optional[str] = None
    supplier: Optional[str] = None


class TypeOfSwabCategoryCreate(TypeOfSwabCategoryBase):
    pass


class TypeOfSwabCategoryUpdate(TypeOfSwabCategoryBase):
    pass


class TypeOfSwabCategoryRead(TypeOfSwabCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
