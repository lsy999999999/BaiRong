from onesim.events import Event
from typing import Dict, List, Any
from datetime import datetime

class BehavioralIntentionCalculatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        behavioral_intentions: float = 0.0,
        TPB_components: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.behavioral_intentions = behavioral_intentions
        self.TPB_components = TPB_components

class IntentionInitializedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ConstraintsAssessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        resource_availability: float = 1.0,
        situational_constraints: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.resource_availability = resource_availability
        self.situational_constraints = situational_constraints

class BehaviorFinalizedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        final_behavior: str = "undetermined",
        completion_status: str = "pending",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.final_behavior = final_behavior
        self.completion_status = completion_status

class SubjectiveNormsAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        adjusted_subjective_norms: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.adjusted_subjective_norms = adjusted_subjective_norms

class SocialNormsEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        social_norms_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.social_norms_score = social_norms_score

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)