from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DeterminationOfSheddingPropensityCategory(Base):
    __tablename__ = "determination_of_shedding_propensity_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    authors: Mapped[Optional[str]]
    title: Mapped[Optional[str]]
    doi: Mapped[Optional[str]]
    restrictions_prior_to_sampling: Mapped[Optional[str]]
    monitored_transfer_factors: Mapped[Optional[str]]
    number_of_participants: Mapped[Optional[str]]
    replicates: Mapped[Optional[str]]
    shedder_test: Mapped[Optional[str]]
    classification_criteria: Mapped[Optional[str]]
    classification_scheme: Mapped[Optional[str]]
    classification_outcome: Mapped[Optional[str]]
