from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class InnovationSpreadEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        innovation_id: str = "",
        network_connections: List[Any] = [],
        relative_advantage: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.innovation_id = innovation_id
        self.network_connections = network_connections
        self.relative_advantage = relative_advantage

class AdoptionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        innovation_id: str = "",
        adoption_rate: float = 0.0,
        social_pressure: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.innovation_id = innovation_id
        self.adoption_rate = adoption_rate
        self.social_pressure = social_pressure

class EarlyMajorityAdoptionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        innovation_id: str = "",
        acceptance_threshold: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.innovation_id = innovation_id
        self.acceptance_threshold = acceptance_threshold

class LateMajorityAdoptionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        innovation_id: str = "",
        influence_factor: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.innovation_id = innovation_id
        self.influence_factor = influence_factor

class LaggardAdoptionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        innovation_id: str = "",
        completion_status: bool = False,
        final_adoption_rate: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.innovation_id = innovation_id
        self.completion_status = completion_status
        self.final_adoption_rate = final_adoption_rate