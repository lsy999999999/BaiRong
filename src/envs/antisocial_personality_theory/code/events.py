from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class InteractionInitiatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class EnvironmentResponseEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        response_type: str = 'neutral',
        response_intensity: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.response_type = response_type
        self.response_intensity = response_intensity

class ManipulationAttemptEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        manipulation_strategy: str = 'coercion',
        target_agent: str = 'unknown',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.manipulation_strategy = manipulation_strategy
        self.target_agent = target_agent

class DisrespectActionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        disrespect_type: str = 'verbal',
        severity_level: int = 1,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.disrespect_type = disrespect_type
        self.severity_level = severity_level

class ManipulationHandledEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        handling_method: str = 'ignore',
        outcome: str = 'unresolved',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.handling_method = handling_method
        self.outcome = outcome

class DisrespectHandledEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        response_action: str = 'reprimand',
        resolution_status: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.response_action = response_action
        self.resolution_status = resolution_status