from typing import Optional

from pydantic import BaseModel, ConfigDict


class LaboratoryBase(BaseModel):
    laboratory_name: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    street_address: Optional[str] = None
    institutional_affiliation: Optional[str] = None
    director_head_of_laboratory: Optional[str] = None
    email: Optional[str] = None


class LaboratoryCreate(LaboratoryBase):
    pass


class LaboratoryUpdate(LaboratoryBase):
    pass


class LaboratoryRead(LaboratoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
