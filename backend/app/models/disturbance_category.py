from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DisturbanceCategory(Base):
    __tablename__ = "disturbance_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    disturbance_category: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
