import enum
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.core.db import Base


class LaboratoryApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"


class Laboratory(Base):
    __tablename__ = "laboratory"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_name: Mapped[str]
    country: Mapped[str]
    postal_code: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    city: Mapped[str]
    street_address: Mapped[Optional[str]]
    institutional_affiliation: Mapped[str]
    director_head_of_laboratory: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
    approval_status: Mapped[LaboratoryApprovalStatus] = mapped_column(
        SAEnum(
            LaboratoryApprovalStatus,
            name="laboratory_approval_status",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        server_default=text("'approved'"),
    )
