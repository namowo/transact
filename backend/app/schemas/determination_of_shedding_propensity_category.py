from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DeterminationOfSheddingPropensityCategoryBase(BaseModel):
    title: Optional[str] = None
    doi: Optional[str] = None
    number_of_participants: Optional[int] = None
    replicates: Optional[int] = None
    classification_criteria_id: Optional[int] = None
    classification_scheme_id: Optional[int] = None
    classification_outcome: Optional[str] = None


class DeterminationOfSheddingPropensityCategoryCreate(
    DeterminationOfSheddingPropensityCategoryBase
):
    authors: List["AuthorCreate"] = []
    restrictions: List["DeterminationOfSheddingPropensityCategoryRestrictionCreate"] = (
        []
    )
    monitored_transfer_factor_ids: List[int] = []
    shedder_tests: List[
        "DeterminationOfSheddingPropensityCategoryShedderTestCreate"
    ] = []


class DeterminationOfSheddingPropensityCategoryUpdate(
    DeterminationOfSheddingPropensityCategoryBase
):
    authors: Optional[List["AuthorCreate"]] = None
    restrictions: Optional[
        List["DeterminationOfSheddingPropensityCategoryRestrictionCreate"]
    ] = None
    monitored_transfer_factor_ids: Optional[List[int]] = None
    shedder_tests: Optional[
        List["DeterminationOfSheddingPropensityCategoryShedderTestCreate"]
    ] = None


class DeterminationOfSheddingPropensityCategoryRead(
    DeterminationOfSheddingPropensityCategoryBase
):
    model_config = ConfigDict(from_attributes=True)

    id: int
    authors: List["AuthorRead"] = []
    restrictions: List["DeterminationOfSheddingPropensityCategoryRestrictionRead"] = []
    monitored_transfer_factors: List["MonitoredTransferFactorRead"] = []
    shedder_tests: List["DeterminationOfSheddingPropensityCategoryShedderTestRead"] = []
    classification_criteria: Optional["ClassificationCriteriaRead"] = None
    classification_scheme: Optional["ClassificationSchemeRead"] = None


from app.schemas.author import AuthorCreate, AuthorRead
from app.schemas.classification_criteria import ClassificationCriteriaRead
from app.schemas.classification_scheme import ClassificationSchemeRead
from app.schemas.determination_of_shedding_propensity_category_restriction import (
    DeterminationOfSheddingPropensityCategoryRestrictionCreate,
    DeterminationOfSheddingPropensityCategoryRestrictionRead,
)
from app.schemas.determination_of_shedding_propensity_category_shedder_test import (
    DeterminationOfSheddingPropensityCategoryShedderTestCreate,
    DeterminationOfSheddingPropensityCategoryShedderTestRead,
)
from app.schemas.monitored_transfer_factor import MonitoredTransferFactorRead
