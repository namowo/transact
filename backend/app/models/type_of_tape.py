from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TypeOfTape(Base):
    __tablename__ = "type_of_tape"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[str]
    description: Mapped[Optional[str]]
