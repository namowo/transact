from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SwabMethodBase(BaseModel):
    wetting_agent_id: Optional[UUID] = None
    volume_of_wetting_agent: Optional[float] = None
    specification: Optional[str] = None
    description: Optional[str] = None
    type_of_swab_category_id: Optional[UUID] = None
    swabbing_technique_category_id: Optional[UUID] = None


class SwabMethodCreate(SwabMethodBase):
    pass


class SwabMethodUpdate(SwabMethodBase):
    pass


class SwabMethodRead(SwabMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type_of_swab_category: Optional["TypeOfSwabCategoryRead"] = None
    swabbing_technique_category: Optional["SwabbingTechniqueCategoryRead"] = None
    wetting_agent: Optional["WettingAgentRead"] = None


from app.schemas.type_of_swab_category import TypeOfSwabCategoryRead
from app.schemas.swabbing_technique_category import SwabbingTechniqueCategoryRead
from app.schemas.wetting_agent import WettingAgentRead
