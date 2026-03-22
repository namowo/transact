from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SwabbingTechniqueCategory(Base):
    __tablename__ = "swabbing_technique_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    swabbing_technique_category: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
