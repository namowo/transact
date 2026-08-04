from datetime import timedelta
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DeterminationOfSheddingPropensityCategoryShedderTest(Base):
    __tablename__ = "determination_of_shedding_propensity_category_shedder_test"

    determination_of_shedding_propensity_category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "determination_of_shedding_propensity_category.id", ondelete="CASCADE"
        ),
        primary_key=True,
    )
    shedder_test_id: Mapped[int] = mapped_column(
        ForeignKey("shedder_test.id", ondelete="CASCADE"), primary_key=True
    )
    duration: Mapped[Optional[timedelta]]
    shedder_test: Mapped["ShedderTest"] = relationship(lazy="selectin")


from app.models.shedder_test import ShedderTest
