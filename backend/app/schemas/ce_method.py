from typing import Optional
from datetime import timedelta

from pydantic import BaseModel, ConfigDict


class CEMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    ce_device: Optional[str] = None
    application_type: Optional[str] = None
    capillary_length: Optional[int] = None
    polymer: Optional[str] = None
    dye_set: Optional[str] = None
    oven_temperature: Optional[float] = None
    run_voltage: Optional[float] = None
    pre_run_voltage: Optional[float] = None
    injection_voltage: Optional[float] = None
    run_time: Optional[timedelta] = None
    pre_run_time: Optional[timedelta] = None
    injection_time: Optional[timedelta] = None
    type_of_formamide: Optional[str] = None
    volume_formamide: Optional[int] = None
    size_standard: Optional[str] = None
    volume_size_standard: Optional[float] = None
    input_volume_pcr_product: Optional[float] = None
    final_volume: Optional[float] = None


class CEMethodCreate(CEMethodBase):
    pass


class CEMethodUpdate(CEMethodBase):
    pass


class CEMethodRead(CEMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
