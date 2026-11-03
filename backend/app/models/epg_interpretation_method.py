import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base

epg_interpretation_method_modelled_parameter = Table(
    "epg_interpretation_method_modelled_parameter",
    Base.metadata,
    Column(
        "epg_interpretation_method_id",
        ForeignKey("epg_interpretation_method.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "modelled_parameter_id",
        ForeignKey("modelled_parameter.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class EPGInterpretationMethod(Base):
    __tablename__ = "epg_interpretation_method"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    laboratory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    determination_of_noc: Mapped[Optional[str]]
    statistical_software_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("statistical_software.id", ondelete="SET NULL")
    )
    statistical_software: Mapped[Optional["StatisticalSoftware"]] = relationship(
        lazy="selectin", foreign_keys=[statistical_software_id]
    )
    modelled_parameters: Mapped[list["ModelledParameter"]] = relationship(
        lazy="selectin",
        secondary=epg_interpretation_method_modelled_parameter,
    )
    allele_frequency_database: Mapped[Optional[str]]
    application_analytical_threshold_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("application_analytical_threshold.id", ondelete="SET NULL")
    )
    application_analytical_threshold: Mapped[
        Optional["ApplicationAnalyticalThreshold"]
    ] = relationship(
        lazy="selectin", foreign_keys=[application_analytical_threshold_id]
    )
    stutter_filter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("stutter_filter.id", ondelete="SET NULL")
    )
    stutter_filter: Mapped[Optional["StutterFilter"]] = relationship(
        lazy="selectin", foreign_keys=[stutter_filter_id]
    )
    description: Mapped[Optional[str]]


from app.models.application_analytical_threshold import ApplicationAnalyticalThreshold
from app.models.laboratory import Laboratory
from app.models.modelled_parameter import ModelledParameter
from app.models.statistical_software import StatisticalSoftware
from app.models.stutter_filter import StutterFilter
