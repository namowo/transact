from typing import Optional

from datetime import datetime
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    # anrede: Mapped[Optional[str]]
    # titel: Mapped[Optional[str]]
    vorname: Mapped[str]
    nachname: Mapped[str]
    telefon: Mapped[Optional[str]]
    organisation: Mapped[str]
    strasse: Mapped[str]
    hausnummer: Mapped[str]
    stadt: Mapped[str]
    plz: Mapped[str]
    land: Mapped[str]

    immobilien: Mapped["Immobilie"] = relationship(back_populates="user")

    erstellt_am: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )


from app.models.immobilie import Immobilie
