from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    item_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item_category.id", ondelete="SET NULL")
    )
    item_category: Mapped[Optional["ItemCategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_category_id]
    )
    item_subcategory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item_subcategory.id", ondelete="SET NULL")
    )
    item_subcategory: Mapped[Optional["ItemSubcategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_subcategory_id]
    )
    description: Mapped[Optional[str]]
    picture_path: Mapped[Optional[str]]


from app.models.item_category import ItemCategory
from app.models.item_subcategory import ItemSubcategory
