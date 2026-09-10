import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class TapeMethod(Base):
    __tablename__ = "tape_method"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    type_of_tape_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("type_of_tape.id", ondelete="SET NULL")
    )
    type_of_tape: Mapped[Optional["TypeOfTape"]] = relationship(
        lazy="selectin", foreign_keys=[type_of_tape_id]
    )
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.type_of_tape import TypeOfTape
from app.models.supplier import Supplier
