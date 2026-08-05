from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SecondsTimedelta


class PCRMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    pcr_kit_id: Optional[int] = None
    thermocycler_id: Optional[int] = None
    initial_denaturation_temp: Optional[float] = None
    initial_denaturation_time: Optional[SecondsTimedelta] = None
    no_of_cycles: Optional[int] = None
    denaturation_temp: Optional[float] = None
    denaturation_time: Optional[SecondsTimedelta] = None
    annealing_temp: Optional[float] = None
    annealing_time: Optional[SecondsTimedelta] = None
    elongation_temp: Optional[float] = None
    elongation_time: Optional[SecondsTimedelta] = None
    final_elongation_temp: Optional[float] = None
    final_elongation_time: Optional[SecondsTimedelta] = None
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
    pcr_kit: Optional["PCRKitRead"] = None
    thermocycler: Optional["ThermocyclerRead"] = None


from app.schemas.laboratory import LaboratoryRead
from app.schemas.pcr_kit import PCRKitRead
from app.schemas.thermocycler import ThermocyclerRead
