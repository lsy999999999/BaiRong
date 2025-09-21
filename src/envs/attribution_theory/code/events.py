from onesim.events import Event
from typing import Any

class AttributionDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        attribution_type: str = 'external',
        reasoning: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.attribution_type = attribution_type
        self.reasoning = reasoning

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class AttributionFeedbackEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        bias_detected: bool = False,
        feedback_message: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.bias_detected = bias_detected
        self.feedback_message = feedback_message

class BehaviorDisplayedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        behavior_type: str = "",
        intended_outcome: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.behavior_type = behavior_type
        self.intended_outcome = intended_outcome

class BehaviorObservedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        behavior_description: str = "",
        observation_context: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.behavior_description = behavior_description
        self.observation_context = observation_context