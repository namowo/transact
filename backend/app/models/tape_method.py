from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TapeMethod(Base):
    __tablename__ = "tape_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    type_of_tape_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("type_of_tape.id", ondelete="SET NULL")
    )
    type_of_tape: Mapped[Optional["TypeOfTape"]] = relationship(
        lazy="selectin", foreign_keys=[type_of_tape_id]
    )
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.type_of_tape import TypeOfTape
from app.models.supplier import Supplier
