from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SecondsTimedelta


class PersistenceBase(BaseModel):
    name: Optional[str] = None
    interval_of_persistence: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    uv_irradiation: Optional[float] = None
    indoors: Optional[bool] = None
    change_over_time: Optional[bool] = None
    duration_of_disturbance: Optional[SecondsTimedelta] = None
    description_of_disturbance: Optional[str] = None
    disturbance_category_id: Optional[int] = None
    geographic_location_category_id: Optional[int] = None


class PersistenceCreate(PersistenceBase):
    # The study this persistence is created for. Only that study may later
    # edit it - it's immutable after creation (not part of PersistenceUpdate).
    owning_study_id: Optional[int] = None


class PersistenceUpdate(PersistenceBase):
    pass


class PersistenceReadNested(PersistenceBase):
    """Persistence as embedded in a ScenarioRead - omits `scenarios` to avoid
    an infinite Scenario <-> Persistence cycle."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owning_study_id: Optional[int] = None
    disturbance_category: Optional["DisturbanceCategoryRead"] = None
    geographic_location_category: Optional["GeographicLocationCategoryRead"] = None


class PersistenceRead(PersistenceReadNested):
    owning_study: Optional["StudyReadNested"] = None
    scenarios: list["ScenarioReadNested"] = []


from app.schemas.disturbance_category import DisturbanceCategoryRead
from app.schemas.geographic_location_category import GeographicLocationCategoryRead
from app.schemas.scenario import ScenarioReadNested
from app.schemas.study import StudyReadNested
