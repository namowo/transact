from typing import Optional

from pydantic import BaseModel, ConfigDict


class SwabMethodBase(BaseModel):
    wetting_agent: Optional[str] = None
    volume_of_wetting_agent: Optional[float] = None
    specification: Optional[str] = None
    description: Optional[str] = None
    type_of_swab_category_id: Optional[int] = None
    swabbing_technique_category_id: Optional[int] = None


class SwabMethodCreate(SwabMethodBase):
    pass


class SwabMethodUpdate(SwabMethodBase):
    pass


class SwabMethodRead(SwabMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type_of_swab_category: Optional["TypeOfSwabCategoryRead"] = None
    swabbing_technique_category: Optional["SwabbingTechniqueCategoryRead"] = None


from app.schemas.type_of_swab_category import TypeOfSwabCategoryRead
from app.schemas.swabbing_technique_category import SwabbingTechniqueCategoryRead
