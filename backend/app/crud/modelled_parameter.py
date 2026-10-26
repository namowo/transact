from app.crud.base import CRUDBase
from app.models.modelled_parameter import ModelledParameter
from app.schemas.modelled_parameter import ModelledParameterCreate, ModelledParameterUpdate


class CRUDModelledParameter(CRUDBase[ModelledParameter, ModelledParameterCreate, ModelledParameterUpdate]):
    def __init__(self):
        super().__init__(ModelledParameter)


crud_modelled_parameter = CRUDModelledParameter()
