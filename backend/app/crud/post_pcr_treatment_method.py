from app.crud.base import CRUDBase
from app.models.post_pcr_treatment_method import PostPCRTreatmentMethod
from app.schemas.post_pcr_treatment_method import PostPCRTreatmentMethodCreate, PostPCRTreatmentMethodUpdate


class CRUDPostPCRTreatmentMethod(CRUDBase[PostPCRTreatmentMethod, PostPCRTreatmentMethodCreate, PostPCRTreatmentMethodUpdate]):
    def __init__(self):
        super().__init__(PostPCRTreatmentMethod)


crud_post_pcr_treatment_method = CRUDPostPCRTreatmentMethod()
