import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class Item(Base):
    __tablename__ = "item"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    item_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("item_category.id", ondelete="SET NULL")
    )
    item_category: Mapped[Optional["ItemCategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_category_id]
    )
    item_subcategory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("item_subcategory.id", ondelete="SET NULL")
    )
    item_subcategory: Mapped[Optional["ItemSubcategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_subcategory_id]
    )
    description: Mapped[Optional[str]]
    picture_path: Mapped[Optional[str]]


from app.models.item_category import ItemCategory
from app.models.item_subcategory import ItemSubcategory
