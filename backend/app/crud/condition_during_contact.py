from app.crud.base import CRUDBase
from app.models.condition_during_contact import ConditionDuringContact
from app.schemas.condition_during_contact import ConditionDuringContactCreate, ConditionDuringContactUpdate


class CRUDConditionDuringContact(CRUDBase[ConditionDuringContact, ConditionDuringContactCreate, ConditionDuringContactUpdate]):
    def __init__(self):
        super().__init__(ConditionDuringContact)


crud_condition_during_contact = CRUDConditionDuringContact()
