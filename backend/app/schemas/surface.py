from typing import Optional

from pydantic import BaseModel, ConfigDict


class SurfaceBase(BaseModel):
    individual_id: Optional[int] = None
    location_of_body_category_id: Optional[int] = None
    body_part_condition_category_id: Optional[int] = None
    item_id: Optional[int] = None
    item_parts_category_id: Optional[int] = None
    condition_of_item_part_category_id: Optional[int] = None
    surface_material_category_id: Optional[int] = None
    source_of_dna_category_id: Optional[int] = None
    photo: Optional[str] = None
    assumed_background_dna: Optional[str] = None
    assumed_prevalence: Optional[bool] = None
    further_description_of_assumed_background_and_prevalence: Optional[str] = None


class SurfaceCreate(SurfaceBase):
    pass


class SurfaceUpdate(SurfaceBase):
    pass


class SurfaceRead(SurfaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    individual: Optional["IndividualRead"] = None
    location_of_body_category: Optional["LocationOfBodyCategoryRead"] = None
    body_part_condition_category: Optional["BodyPartConditionCategoryRead"] = None
    item: Optional["ItemRead"] = None
    item_parts_category: Optional["ItemPartsCategoryRead"] = None
    condition_of_item_part_category: Optional["ConditionOfItemPartCategoryRead"] = None
    surface_material_category: Optional["SurfaceMaterialCategoryRead"] = None
    source_of_dna_category: Optional["SourceOfDNACategoryRead"] = None


from app.schemas.individual import IndividualRead
from app.schemas.location_of_body_category import LocationOfBodyCategoryRead
from app.schemas.body_part_condition_category import BodyPartConditionCategoryRead
from app.schemas.item import ItemRead
from app.schemas.item_parts_category import ItemPartsCategoryRead
from app.schemas.condition_of_item_part_category import ConditionOfItemPartCategoryRead
from app.schemas.surface_material_category import SurfaceMaterialCategoryRead
from app.schemas.source_of_dna_category import SourceOfDNACategoryRead
