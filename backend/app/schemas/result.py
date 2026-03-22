from typing import Optional

from pydantic import BaseModel, ConfigDict


class ResultBase(BaseModel):
    quantification_method_id: Optional[int] = None
    recovery_id: Optional[int] = None
    dna_concentration: Optional[int] = None
    degradation: Optional[str] = None
    inhibition: Optional[str] = None
    dna_quantity: Optional[int] = None
    pcr_method_id: Optional[int] = None
    sample_input_volume_in_pcr: Optional[int] = None
    dna_input_amount_in_pcr: Optional[int] = None
    post_pcr_treatment_method_id: Optional[int] = None
    ce_method_id: Optional[int] = None
    epg_analysis_method_id: Optional[int] = None
    epg_interpretation_method_id: Optional[int] = None
    no_of_contributors: Optional[str] = None
    mixture_proportion: Optional[str] = None
    total_rfu: Optional[str] = None
    total_no_of_alleles: Optional[str] = None


class ResultCreate(ResultBase):
    pass


class ResultUpdate(ResultBase):
    pass


class ResultRead(ResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantification_method: Optional["QuantificationMethodRead"] = None
    recovery: Optional["RecoveryRead"] = None
    pcr_method: Optional["PCRMethodRead"] = None
    post_pcr_treatment_method: Optional["PostPCRTreatmentMethodRead"] = None
    ce_method: Optional["CEMethodRead"] = None
    epg_analysis_method: Optional["EPGAnalysisMethodRead"] = None
    epg_interpretation_method: Optional["EPGInterpretationMethodRead"] = None


from app.schemas.quantification_method import QuantificationMethodRead
from app.schemas.recovery import RecoveryRead
from app.schemas.pcr_method import PCRMethodRead
from app.schemas.post_pcr_treatment_method import PostPCRTreatmentMethodRead
from app.schemas.ce_method import CEMethodRead
from app.schemas.epg_analysis_method import EPGAnalysisMethodRead
from app.schemas.epg_interpretation_method import EPGInterpretationMethodRead
