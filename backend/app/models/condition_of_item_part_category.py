from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ConditionOfItemPartCategory(Base):
    __tablename__ = "condition_of_item_part_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    condition_of_item_part_category: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
