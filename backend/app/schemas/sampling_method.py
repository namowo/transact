from typing import Optional

from pydantic import BaseModel, ConfigDict


class SamplingMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    swab_method_id: Optional[int] = None
    tape_method_id: Optional[int] = None
    vacuum_method_id: Optional[int] = None
    cutting_method_id: Optional[int] = None
    scraping_method_id: Optional[int] = None
    picking_method_id: Optional[int] = None


class SamplingMethodCreate(SamplingMethodBase):
    pass


class SamplingMethodUpdate(SamplingMethodBase):
    pass


class SamplingMethodRead(SamplingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None
    swab_method: Optional["SwabMethodRead"] = None
    tape_method: Optional["TapeMethodRead"] = None
    vacuum_method: Optional["VacuumMethodRead"] = None
    cutting_method: Optional["CuttingMethodRead"] = None
    scraping_method: Optional["ScrapingMethodRead"] = None
    picking_method: Optional["PickingMethodRead"] = None


from app.schemas.laboratory import LaboratoryRead
from app.schemas.swab_method import SwabMethodRead
from app.schemas.tape_method import TapeMethodRead
from app.schemas.vacuum_method import VacuumMethodRead
from app.schemas.cutting_method import CuttingMethodRead
from app.schemas.scraping_method import ScrapingMethodRead
from app.schemas.picking_method import PickingMethodRead
