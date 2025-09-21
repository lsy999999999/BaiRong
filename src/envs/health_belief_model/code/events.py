from onesim.events import Event
from typing import Any, List, Optional

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class HealthThreatEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        threat_level: float = 0.0,
        susceptibility: float = 0.0,
        severity: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.threat_level = threat_level
        self.susceptibility = susceptibility
        self.severity = severity

class HealthBehaviorAdoptedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        behavior_type: str = 'unknown',
        success: bool = False,
        barriers_overcome: Optional[List[Any]] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.behavior_type = behavior_type
        self.success = success
        self.barriers_overcome = barriers_overcome if barriers_overcome is not None else []

class SupportProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        support_type: str = 'emotional',
        intensity: int = 1,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.support_type = support_type
        self.intensity = intensity

class NormsEstablishedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        norm_description: str = 'undefined',
        acceptance_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.norm_description = norm_description
        self.acceptance_level = acceptance_level

class PolicyImplementedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        policy_name: str = 'unknown',
        impact_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.policy_name = policy_name
        self.impact_level = impact_level