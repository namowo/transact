from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SampleBase(BaseModel):
    name: Optional[str] = None
    study_id: Optional[UUID] = None
    sample_set_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    surface_id: Optional[UUID] = None
    sampling_method_id: Optional[UUID] = None
    extraction_method_id: Optional[UUID] = None
    elution_volume: Optional[float] = None
    area: Optional[float] = None
    experience_level_of_sampler_id: Optional[UUID] = None


class SampleCreate(SampleBase):
    pass


class SampleUpdate(SampleBase):
    pass


class SampleRead(SampleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sample_set: Optional["SampleSetRead"] = None
    surface: Optional["SurfaceRead"] = None
    sampling_method: Optional["SamplingMethodRead"] = None
    extraction_method: Optional["ExtractionMethodRead"] = None
    experience_level_of_sampler: Optional["ExperienceLevelRead"] = None


from app.schemas.sample_set import SampleSetRead
from app.schemas.surface import SurfaceRead
from app.schemas.sampling_method import SamplingMethodRead
from app.schemas.extraction_method import ExtractionMethodRead
from app.schemas.experience_level import ExperienceLevelRead
