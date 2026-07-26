from app.crud.base import CRUDBase
from app.models.dna_shedding_propensity_category import DNASheddingPropensityCategory
from app.schemas.dna_shedding_propensity_category import (
    DNASheddingPropensityCategoryCreate,
    DNASheddingPropensityCategoryUpdate,
)


class CRUDDNASheddingPropensityCategory(
    CRUDBase[
        DNASheddingPropensityCategory,
        DNASheddingPropensityCategoryCreate,
        DNASheddingPropensityCategoryUpdate,
    ]
):
    def __init__(self):
        super().__init__(DNASheddingPropensityCategory)


crud_dna_shedding_propensity_category = CRUDDNASheddingPropensityCategory()
