from datetime import timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DeterminationOfSheddingPropensityCategoryShedderTestBase(BaseModel):
    shedder_test_id: int
    duration: Optional[timedelta] = None


class DeterminationOfSheddingPropensityCategoryShedderTestCreate(
    DeterminationOfSheddingPropensityCategoryShedderTestBase
):
    pass


class DeterminationOfSheddingPropensityCategoryShedderTestRead(
    DeterminationOfSheddingPropensityCategoryShedderTestBase
):
    model_config = ConfigDict(from_attributes=True)

    shedder_test: Optional["ShedderTestRead"] = None


from app.schemas.shedder_test import ShedderTestRead
