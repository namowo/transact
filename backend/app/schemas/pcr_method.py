from typing import Optional

from pydantic import BaseModel, ConfigDict


class PCRMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    pcr_kit: Optional[str] = None
    thermocycler: Optional[str] = None
    initial_denaturation_temp: Optional[int] = None
    initial_denaturation_time: Optional[int] = None
    no_of_cycles: Optional[int] = None
    denaturation_temp: Optional[int] = None
    denaturation_time: Optional[int] = None
    annealing_temp: Optional[int] = None
    annealing_time: Optional[int] = None
    elongation_temp: Optional[int] = None
    elongation_time: Optional[int] = None
    final_elongation_temp: Optional[int] = None
    final_elongation_time: Optional[int] = None
    ramping: Optional[int] = None
    total_volume_pcr_reaction: Optional[int] = None


class PCRMethodCreate(PCRMethodBase):
    pass


class PCRMethodUpdate(PCRMethodBase):
    pass


class PCRMethodRead(PCRMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
