from app.crud.base import CRUDBase
from app.models.experience_level import ExperienceLevel
from app.schemas.experience_level import ExperienceLevelCreate, ExperienceLevelUpdate


class CRUDExperienceLevel(CRUDBase[ExperienceLevel, ExperienceLevelCreate, ExperienceLevelUpdate]):
    def __init__(self):
        super().__init__(ExperienceLevel)


crud_experience_level = CRUDExperienceLevel()
