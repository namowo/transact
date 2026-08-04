from app.crud.base import CRUDBase
from app.models.shedder_test import ShedderTest
from app.schemas.shedder_test import ShedderTestCreate, ShedderTestUpdate


class CRUDShedderTest(CRUDBase[ShedderTest, ShedderTestCreate, ShedderTestUpdate]):
    def __init__(self):
        super().__init__(ShedderTest)


crud_shedder_test = CRUDShedderTest()
