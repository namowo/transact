from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class BodyPartConditionCategory(Base):
    __tablename__ = "body_part_condition_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    body_part_condition_category: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
