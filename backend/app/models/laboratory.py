from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Laboratory(Base):
    __tablename__ = "laboratory"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_name: Mapped[Optional[str]]
    country: Mapped[Optional[str]]
    postal_code: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    city: Mapped[Optional[str]]
    street_address: Mapped[Optional[str]]
    institutional_affiliation: Mapped[Optional[str]]
    director_head_of_laboratory: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
