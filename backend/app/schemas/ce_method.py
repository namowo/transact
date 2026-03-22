from typing import Optional

from pydantic import BaseModel, ConfigDict


class CEMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    ce_device: Optional[str] = None
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
    application_type: Optional[str] = None
    capillary_length: Optional[str] = None
    polymer: Optional[str] = None
    dye_set: Optional[str] = None
    oven_temperature: Optional[str] = None
    run_voltage: Optional[str] = None
    pre_run_voltage: Optional[str] = None
    injection_voltage: Optional[str] = None
    run_time: Optional[str] = None
    pre_run_time: Optional[str] = None
    injection_time: Optional[str] = None
    type_of_formamide: Optional[str] = None
    volume_formamide: Optional[str] = None
    size_standard: Optional[str] = None
    volume_size_standard: Optional[str] = None
    input_volume_pcr_product: Optional[str] = None
    final_volume: Optional[str] = None


class CEMethodCreate(CEMethodBase):
    pass


class CEMethodUpdate(CEMethodBase):
    pass


class CEMethodRead(CEMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
