from typing import Optional
from datetime import timedelta

from pydantic import BaseModel, ConfigDict


class PCRMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    pcr_kit: Optional[str] = None
    thermocycler: Optional[str] = None
    initial_denaturation_temp: Optional[float] = None
    initial_denaturation_time: Optional[timedelta] = None
    no_of_cycles: Optional[int] = None
    denaturation_temp: Optional[float] = None
    denaturation_time: Optional[timedelta] = None
    annealing_temp: Optional[float] = None
    annealing_time: Optional[timedelta] = None
    elongation_temp: Optional[float] = None
    elongation_time: Optional[timedelta] = None
    final_elongation_temp: Optional[float] = None
    final_elongation_time: Optional[timedelta] = None
    ramping: Optional[float] = None
    total_volume_pcr_reaction: Optional[float] = None


class PCRMethodCreate(PCRMethodBase):
    pass


class PCRMethodUpdate(PCRMethodBase):
    pass


class PCRMethodRead(PCRMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
