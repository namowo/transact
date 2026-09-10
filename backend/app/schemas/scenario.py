from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ScenarioBase(BaseModel):
    realistic: Optional[bool] = None
    scenario_category_id: Optional[UUID] = None


class ScenarioCreate(ScenarioBase):
    # The study this scenario is created for. Only that study may later
    # edit it - it's immutable after creation (not part of ScenarioUpdate).
    owning_study_id: Optional[UUID] = None
    study_ids: list[UUID] = []
    contact_template_ids: list[UUID] = []
    persistence_ids: list[UUID] = []


class ScenarioUpdate(ScenarioBase):
    study_ids: Optional[list[UUID]] = None
    contact_template_ids: Optional[list[UUID]] = None
    persistence_ids: Optional[list[UUID]] = None


class ScenarioReadNested(ScenarioBase):
    """Scenario as embedded in a StudyRead or PersistenceRead - omits
    `studies` and `persistencies` to avoid infinite Study/Persistence <->
    Scenario cycles."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owning_study_id: Optional[UUID] = None
    scenario_category: Optional["ScenarioCategoryRead"] = None
    contact_templates: list["ContactTemplateRead"] = []


class ScenarioRead(ScenarioReadNested):
    studies: list["StudyReadNested"] = []
    persistencies: list["PersistenceReadNested"] = []


from app.schemas.scenario_category import ScenarioCategoryRead
from app.schemas.study import StudyReadNested
from app.schemas.contact_template import ContactTemplateRead
from app.schemas.persistence import PersistenceReadNested
