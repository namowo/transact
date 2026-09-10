import uuid
from datetime import timedelta
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DeterminationOfSheddingPropensityCategoryRestriction(Base):
    __tablename__ = "determination_of_shedding_propensity_category_restriction"

    determination_of_shedding_propensity_category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "determination_of_shedding_propensity_category.id", ondelete="CASCADE"
        ),
        primary_key=True,
    )
    restriction_prior_to_sampling_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("restriction_prior_to_sampling.id", ondelete="CASCADE"),
        primary_key=True,
    )
    duration: Mapped[Optional[timedelta]]
    restriction_prior_to_sampling: Mapped["RestrictionPriorToSampling"] = relationship(
        lazy="selectin"
    )


from app.models.restriction_prior_to_sampling import RestrictionPriorToSampling
