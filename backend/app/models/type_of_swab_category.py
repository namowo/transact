from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TypeOfSwabCategory(Base):
    __tablename__ = "type_of_swab_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.supplier import Supplier
