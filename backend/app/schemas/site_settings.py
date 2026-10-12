from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

LegalPageMode = Literal["text", "url"]


class SiteSettingsBase(BaseModel):
    site_print_mode: LegalPageMode = "text"
    site_print_text: Optional[str] = None
    site_print_url: Optional[str] = None

    privacy_policy_mode: LegalPageMode = "text"
    privacy_policy_text: Optional[str] = None
    privacy_policy_url: Optional[str] = None


class SiteSettingsUpdate(BaseModel):
    site_print_mode: Optional[LegalPageMode] = None
    site_print_text: Optional[str] = None
    site_print_url: Optional[str] = None

    privacy_policy_mode: Optional[LegalPageMode] = None
    privacy_policy_text: Optional[str] = None
    privacy_policy_url: Optional[str] = None


class SiteSettingsRead(SiteSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
