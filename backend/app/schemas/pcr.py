from typing import List, Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_CONTRIBUTORS = 8
# Absorbs rounding to 5 decimals (e.g. 3 x 0.33333).
MIXTURE_SUM_TOLERANCE = 1e-4


class PCRBase(BaseModel):
    pcr_method_id: Optional[UUID] = None
    sample_input_volume_in_pcr: Optional[float] = None
    dna_input_amount_in_pcr: Optional[float] = None
    post_pcr_treatment_method_id: Optional[UUID] = None
    ce_method_id: Optional[UUID] = None
    epg_analysis_method_id: Optional[UUID] = None
    epg_interpretation_method_id: Optional[UUID] = None
    no_of_contributors: Optional[int] = None
    total_rfu: Optional[int] = None
    total_no_of_alleles: Optional[int] = None


class PCRCreate(PCRBase):
    # Limits apply on write only, so reading older rows never fails.
    no_of_contributors: Optional[int] = Field(default=None, ge=0, le=MAX_CONTRIBUTORS)
    contributors: List["PCRContributorCreate"] = Field(default=[], max_length=MAX_CONTRIBUTORS)

    @model_validator(mode="after")
    def _unique_contributors(self):
        individuals = [c.individual_id for c in self.contributors if c.individual_id is not None]
        unknowns = [c.unknown_label for c in self.contributors if c.unknown_label is not None]
        if len(individuals) != len(set(individuals)) or len(unknowns) != len(set(unknowns)):
            raise ValueError("Each contributor can only be selected once.")
        return self

    @model_validator(mode="after")
    def _mixture_proportions_sum_to_one(self):
        # Never more than 1 in total; exactly 1 once every contributor has one.
        proportions = [c.mixture_proportion for c in self.contributors]
        filled = [p for p in proportions if p is not None]
        if filled:
            total = sum(filled)
            complete = len(filled) == len(proportions)
            if total > 1 + MIXTURE_SUM_TOLERANCE or (complete and total < 1 - MIXTURE_SUM_TOLERANCE):
                raise ValueError(f"Mixture proportions must add up to 1 (currently {round(total, 5)}).")
        return self


class PCRRead(PCRBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pcr_method: Optional["PCRMethodRead"] = None
    post_pcr_treatment_method: Optional["PostPCRTreatmentMethodRead"] = None
    ce_method: Optional["CEMethodRead"] = None
    epg_analysis_method: Optional["EPGAnalysisMethodRead"] = None
    epg_interpretation_method: Optional["EPGInterpretationMethodRead"] = None
    contributors: List["PCRContributorRead"] = []


from app.schemas.pcr_method import PCRMethodRead
from app.schemas.post_pcr_treatment_method import PostPCRTreatmentMethodRead
from app.schemas.ce_method import CEMethodRead
from app.schemas.epg_analysis_method import EPGAnalysisMethodRead
from app.schemas.epg_interpretation_method import EPGInterpretationMethodRead
from app.schemas.pcr_contributor import PCRContributorCreate, PCRContributorRead
