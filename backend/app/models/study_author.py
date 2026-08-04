from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class StudyAuthor(Base):
    __tablename__ = "study_author"

    study_id: Mapped[int] = mapped_column(
        ForeignKey("study.id", ondelete="CASCADE"), primary_key=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("author.id", ondelete="CASCADE"), primary_key=True
    )
    # Preserves author order as entered; not an academic "authorship position".
    position: Mapped[int]
    author: Mapped["Author"] = relationship(lazy="selectin")


from app.models.author import Author
