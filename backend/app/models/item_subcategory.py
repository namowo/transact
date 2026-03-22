from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ItemSubcategory(Base):
    __tablename__ = "item_subcategory"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    item_subcategory: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
