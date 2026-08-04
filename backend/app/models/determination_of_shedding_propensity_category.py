from typing import Optional

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

determination_of_shedding_propensity_category_author = Table(
    "determination_of_shedding_propensity_category_author",
    Base.metadata,
    Column(
        "determination_of_shedding_propensity_category_id",
        ForeignKey(
            "determination_of_shedding_propensity_category.id", ondelete="CASCADE"
        ),
        primary_key=True,
    ),
    Column("author_id", ForeignKey("author.id", ondelete="CASCADE"), primary_key=True),
)

determination_of_shedding_propensity_category_monitored_transfer_factor = Table(
    "det_shedding_propensity_category_transfer_factor",
    Base.metadata,
    Column(
        "determination_of_shedding_propensity_category_id",
        ForeignKey(
            "determination_of_shedding_propensity_category.id", ondelete="CASCADE"
        ),
        primary_key=True,
    ),
    Column(
        "monitored_transfer_factor_id",
        ForeignKey("monitored_transfer_factor.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class DeterminationOfSheddingPropensityCategory(Base):
    __tablename__ = "determination_of_shedding_propensity_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    title: Mapped[Optional[str]]
    doi: Mapped[Optional[str]]
    authors: Mapped[list["Author"]] = relationship(
        lazy="selectin",
        secondary=determination_of_shedding_propensity_category_author,
    )
    restrictions: Mapped[
        list["DeterminationOfSheddingPropensityCategoryRestriction"]
    ] = relationship(lazy="selectin", cascade="all, delete-orphan")
    monitored_transfer_factors: Mapped[list["MonitoredTransferFactor"]] = relationship(
        lazy="selectin",
        secondary=determination_of_shedding_propensity_category_monitored_transfer_factor,
    )
    number_of_participants: Mapped[Optional[int]]
    replicates: Mapped[Optional[int]]
    shedder_tests: Mapped[list["DeterminationOfSheddingPropensityCategoryShedderTest"]] = (
        relationship(lazy="selectin", cascade="all, delete-orphan")
    )
    classification_criteria_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("classification_criteria.id", ondelete="SET NULL")
    )
    classification_criteria: Mapped[Optional["ClassificationCriteria"]] = relationship(
        lazy="selectin", foreign_keys=[classification_criteria_id]
    )
    classification_scheme_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("classification_scheme.id", ondelete="SET NULL")
    )
    classification_scheme: Mapped[Optional["ClassificationScheme"]] = relationship(
        lazy="selectin", foreign_keys=[classification_scheme_id]
    )
    classification_outcome: Mapped[Optional[str]]


from app.models.author import Author
from app.models.classification_criteria import ClassificationCriteria
from app.models.classification_scheme import ClassificationScheme
from app.models.determination_of_shedding_propensity_category_restriction import (
    DeterminationOfSheddingPropensityCategoryRestriction,
)
from app.models.determination_of_shedding_propensity_category_shedder_test import (
    DeterminationOfSheddingPropensityCategoryShedderTest,
)
from app.models.monitored_transfer_factor import MonitoredTransferFactor
