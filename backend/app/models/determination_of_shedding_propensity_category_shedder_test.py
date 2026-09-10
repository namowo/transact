import uuid
from datetime import timedelta
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DeterminationOfSheddingPropensityCategoryShedderTest(Base):
    __tablename__ = "determination_of_shedding_propensity_category_shedder_test"

    determination_of_shedding_propensity_category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "determination_of_shedding_propensity_category.id", ondelete="CASCADE"
        ),
        primary_key=True,
    )
    shedder_test_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("shedder_test.id", ondelete="CASCADE"), primary_key=True
    )
    duration: Mapped[Optional[timedelta]]
    shedder_test: Mapped["ShedderTest"] = relationship(lazy="selectin")


from app.models.shedder_test import ShedderTest
