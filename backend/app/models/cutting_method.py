from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CuttingMethod(Base):
    __tablename__ = "cutting_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    cutting_device: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    catalogue_number_of_supplier: Mapped[Optional[str]]
    full_name_as_by_supplier: Mapped[Optional[str]]
    supplier: Mapped[Optional[str]]
