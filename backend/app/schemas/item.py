from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    item_category_id: Optional[UUID] = None
    item_subcategory_id: Optional[UUID] = None
    description: Optional[str] = None
    picture_path: Optional[str] = None


class ItemCreate(ItemBase):
    # Items live in a shared catalog; each study explicitly adds the
    # specific items it uses.
    study_ids: list[UUID] = []


class ItemUpdate(ItemBase):
    study_ids: Optional[list[UUID]] = None


class ItemReadNested(ItemBase):
    """Item as embedded in a SurfaceTemplateRead/SurfaceRead - omits
    `studies` since those requests don't need it and the nesting can run
    many levels deep (Study -> Scenario -> ... -> SurfaceTemplate -> Item),
    too deep for the `studies` relationship to lazy-load during response
    serialization."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_category: Optional["ItemCategoryRead"] = None
    item_subcategory: Optional["ItemSubcategoryRead"] = None


class ItemRead(ItemReadNested):
    studies: list["StudyReadNested"] = []


class ItemGroup(BaseModel):
    """Items grouped by category, shaped for a PrimeVue Select's
    optionGroupLabel/optionGroupChildren."""

    label: str
    value: Optional[UUID] = None
    items: list[ItemReadNested]


from app.schemas.item_category import ItemCategoryRead
from app.schemas.item_subcategory import ItemSubcategoryRead
from app.schemas.study import StudyReadNested
