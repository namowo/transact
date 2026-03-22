from app.crud.base import CRUDBase
from app.models.source_of_dna_category import SourceOfDNACategory
from app.schemas.source_of_dna_category import SourceOfDNACategoryCreate, SourceOfDNACategoryUpdate


class CRUDSourceOfDNACategory(CRUDBase[SourceOfDNACategory, SourceOfDNACategoryCreate, SourceOfDNACategoryUpdate]):
    def __init__(self):
        super().__init__(SourceOfDNACategory)


crud_source_of_dna_category = CRUDSourceOfDNACategory()
