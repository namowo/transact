from typing import Optional

from pydantic import BaseModel, ConfigDict


class EPGInterpretationMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    determination_of_noc: Optional[str] = None
    statistical_software: Optional[str] = None
    parameters_modelled_by_software: Optional[str] = None
    allele_frequency_database: Optional[str] = None


class EPGInterpretationMethodCreate(EPGInterpretationMethodBase):
    pass


class EPGInterpretationMethodUpdate(EPGInterpretationMethodBase):
    pass


class EPGInterpretationMethodRead(EPGInterpretationMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
