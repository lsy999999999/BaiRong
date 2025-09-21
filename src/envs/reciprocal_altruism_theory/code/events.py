from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class BehaviorChangeInitiatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        advocate_id: str = "",
        recipient_id: str = "",
        behavior_type: str = 'generic_behavior',
        intensity: int = 1,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.advocate_id = advocate_id
        self.recipient_id = recipient_id
        self.behavior_type = behavior_type
        self.intensity = intensity

class CommitToSpreadEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        recipient_id: str = "",
        commitment_level: int = 1,
        spread_target: str = 'community',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.recipient_id = recipient_id
        self.commitment_level = commitment_level
        self.spread_target = spread_target

class BehaviorSpreadEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        network_id: str = "",
        spread_result: str = 'success',
        completion_status: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.network_id = network_id
        self.spread_result = spread_result
        self.completion_status = completion_status