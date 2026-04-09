from typing import Optional
from datetime import timedelta

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ConditionDuringContact(Base):
    __tablename__ = "condition_during_contact"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    temperature: Mapped[Optional[float]]
    humidity: Mapped[Optional[float]]
    uv_irradiation: Mapped[Optional[float]]
    indoors: Mapped[Optional[bool]]
    change_over_time: Mapped[Optional[bool]]
    duration_of_disturbance: Mapped[Optional[timedelta]]
    description_of_disturbance: Mapped[Optional[str]]
    disturbance_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("disturbance_category.id", ondelete="SET NULL")
    )
    disturbance_category: Mapped[Optional["DisturbanceCategory"]] = relationship(
        lazy="selectin", foreign_keys=[disturbance_category_id]
    )
    geographic_location_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("geographic_location_category.id", ondelete="SET NULL")
    )
    geographic_location_category: Mapped[Optional["GeographicLocationCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[geographic_location_category_id])
    )


from app.models.disturbance_category import DisturbanceCategory
from app.models.geographic_location_category import GeographicLocationCategory
