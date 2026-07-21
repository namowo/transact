from typing import Optional

from pydantic import BaseModel, ConfigDict


class RecoveryBase(BaseModel):
    surface_id: Optional[int] = None
    sampling_method_id: Optional[int] = None
    extraction_method_id: Optional[int] = None
    elution_volume: Optional[float] = None
    area: Optional[float] = None
    experience_level_of_sampler_id: Optional[int] = None


class RecoveryCreate(RecoveryBase):
    pass


class RecoveryUpdate(RecoveryBase):
    pass


class RecoveryRead(RecoveryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    surface: Optional["SurfaceRead"] = None
    sampling_method: Optional["SamplingMethodRead"] = None
    extraction_method: Optional["ExtractionMethodRead"] = None
    experience_level_of_sampler: Optional["ExperienceLevelRead"] = None


from app.schemas.surface import SurfaceRead
from app.schemas.sampling_method import SamplingMethodRead
from app.schemas.extraction_method import ExtractionMethodRead
from app.schemas.experience_level import ExperienceLevelRead
