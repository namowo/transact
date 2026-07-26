from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScenarioBase(BaseModel):
    realistic: Optional[bool] = None
    scenario_category_id: Optional[int] = None


class ScenarioCreate(ScenarioBase):
    study_ids: list[int] = []
    contact_template_ids: list[int] = []
    persistence_ids: list[int] = []


class ScenarioUpdate(ScenarioBase):
    study_ids: Optional[list[int]] = None
    contact_template_ids: Optional[list[int]] = None
    persistence_ids: Optional[list[int]] = None


class ScenarioRead(ScenarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_category: Optional["ScenarioCategoryRead"] = None
    studies: list["StudyRead"] = []
    contact_templates: list["ContactTemplateRead"] = []
    persistencies: list["PersistenceRead"] = []


from app.schemas.scenario_category import ScenarioCategoryRead
from app.schemas.study import StudyRead
from app.schemas.contact_template import ContactTemplateRead
from app.schemas.persistence import PersistenceRead
