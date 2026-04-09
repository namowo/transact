from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Laboratory(Base):
    __tablename__ = "laboratory"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_name: Mapped[str]
    country: Mapped[str]
    postal_code: Mapped[str]
    state: Mapped[str]
    city: Mapped[str]
    street_address: Mapped[str]
    institutional_affiliation: Mapped[str]
    director_head_of_laboratory: Mapped[str]
    email: Mapped[str]
