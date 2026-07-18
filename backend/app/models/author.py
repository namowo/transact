from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    study_id: Mapped[int] = mapped_column(
        ForeignKey("study.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[Optional[str]]
    first_name: Mapped[str]
    last_name: Mapped[str]
    # Preserves author order as entered; not an academic "authorship position".
    position: Mapped[int]
