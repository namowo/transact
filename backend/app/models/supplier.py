from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Supplier(Base):
    __tablename__ = "supplier"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
    catalogue_number_of_supplier: Mapped[Optional[str]]
    full_name_as_by_supplier: Mapped[Optional[str]]
