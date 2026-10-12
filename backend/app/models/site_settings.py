from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    site_print_mode: Mapped[str] = mapped_column(default="text", server_default="text")
    site_print_text: Mapped[Optional[str]]
    site_print_url: Mapped[Optional[str]]

    privacy_policy_mode: Mapped[str] = mapped_column(default="text", server_default="text")
    privacy_policy_text: Mapped[Optional[str]]
    privacy_policy_url: Mapped[Optional[str]]
