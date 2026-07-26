from app.crud.base import CRUDBase
from app.models.wetting_agent import WettingAgent
from app.schemas.wetting_agent import WettingAgentCreate, WettingAgentUpdate


class CRUDWettingAgent(CRUDBase[WettingAgent, WettingAgentCreate, WettingAgentUpdate]):
    def __init__(self):
        super().__init__(WettingAgent)


crud_wetting_agent = CRUDWettingAgent()
