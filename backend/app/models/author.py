from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    title: Mapped[Optional[str]]
    first_name: Mapped[str]
    last_name: Mapped[str]
