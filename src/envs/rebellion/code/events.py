from onesim.events import Event
from typing import Any

class GrievanceEvaluatedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 grievance_level: float = 0.0,
                 citizen_id: str = "N/A",
                 **kwargs: Any
                 ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.grievance_level = grievance_level
        self.citizen_id = citizen_id

class RepressionImplementedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 repression_strategy: str = "none",
                 effectiveness: float = 0.0,
                 government_id: str = "N/A",
                 **kwargs: Any
                 ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.repression_strategy = repression_strategy
        self.effectiveness = effectiveness
        self.government_id = government_id

class NoRebellionEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 citizen_id: str = "N/A",
                 decision: bool = True,
                 **kwargs: Any
                 ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.citizen_id = citizen_id
        self.decision = decision

class RebellionAssessedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 rebellion_level: float = 0.0,
                 government_id: str = "N/A",
                 **kwargs: Any
                 ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.rebellion_level = rebellion_level
        self.government_id = government_id

class RebellionDecisionEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 citizen_id: str = "N/A",
                 decision: bool = False,
                 **kwargs: Any
                 ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.citizen_id = citizen_id
        self.decision = decision

class StartEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 **kwargs: Any
                 ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)