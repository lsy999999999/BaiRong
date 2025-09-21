from onesim.events import Event
from typing import Dict, List, Any
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class CooperationDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        cooperation_willingness: float = 0.0,
        personal_cost: float = 0.0,
        personal_benefit: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.cooperation_willingness = cooperation_willingness
        self.personal_cost = personal_cost
        self.personal_benefit = personal_benefit

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class CollectiveActionResultEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        collective_success: bool = False,
        total_cooperation: float = 0.0,
        group_benefit: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.collective_success = collective_success
        self.total_cooperation = total_cooperation
        self.group_benefit = group_benefit
