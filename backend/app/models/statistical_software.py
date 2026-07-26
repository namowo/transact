from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StatisticalSoftware(Base):
    __tablename__ = "statistical_software"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
