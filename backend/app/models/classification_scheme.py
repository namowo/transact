from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ClassificationScheme(Base):
    __tablename__ = "classification_scheme"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
