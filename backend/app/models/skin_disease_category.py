from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SkinDiseaseCategory(Base):
    __tablename__ = "skin_disease_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    skin_disease_category: Mapped[Optional[str]]
    influence_on_shedding_propensity: Mapped[Optional[str]]
    literature: Mapped[Optional[str]]
