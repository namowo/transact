from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ItemSubcategory(Base):
    __tablename__ = "item_subcategory"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    item_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item_category.id", ondelete="SET NULL")
    )
    item_category: Mapped[Optional["ItemCategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_category_id]
    )


from app.models.item_category import ItemCategory
