from app.crud.base import CRUDBase
from app.models.genotyping_software import GenotypingSoftware
from app.schemas.genotyping_software import GenotypingSoftwareCreate, GenotypingSoftwareUpdate


class CRUDGenotypingSoftware(CRUDBase[GenotypingSoftware, GenotypingSoftwareCreate, GenotypingSoftwareUpdate]):
    def __init__(self):
        super().__init__(GenotypingSoftware)


crud_genotyping_software = CRUDGenotypingSoftware()
