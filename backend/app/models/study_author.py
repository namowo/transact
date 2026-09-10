import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class StudyAuthor(Base):
    __tablename__ = "study_author"

    study_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("study.id", ondelete="CASCADE"), primary_key=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("author.id", ondelete="CASCADE"), primary_key=True
    )
    # Preserves author order as entered; not an academic "authorship position".
    position: Mapped[int]
    author: Mapped["Author"] = relationship(lazy="selectin")


from app.models.author import Author
