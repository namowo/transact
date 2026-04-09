from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PrincipleOfQuantMethodCategory(Base):
    __tablename__ = "principle_of_quant_method_category"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
