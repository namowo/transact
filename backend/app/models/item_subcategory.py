import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class ItemSubcategory(Base):
    __tablename__ = "item_subcategory"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    item_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("item_category.id", ondelete="SET NULL")
    )
    item_category: Mapped[Optional["ItemCategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_category_id]
    )


from app.models.item_category import ItemCategory
