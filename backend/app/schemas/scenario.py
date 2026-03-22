from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScenarioBase(BaseModel):
    realistic: Optional[bool] = None
    scenario_category_id: Optional[int] = None
    study_id: Optional[int] = None
    contact_id: Optional[int] = None
    persistence_id: Optional[int] = None


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(ScenarioBase):
    pass


class ScenarioRead(ScenarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_category: Optional["ScenarioCategoryRead"] = None
    study: Optional["StudyRead"] = None
    contact: Optional["ContactRead"] = None
    persistence: Optional["PersistenceRead"] = None


from app.schemas.scenario_category import ScenarioCategoryRead
from app.schemas.study import StudyRead
from app.schemas.contact import ContactRead
from app.schemas.persistence import PersistenceRead
