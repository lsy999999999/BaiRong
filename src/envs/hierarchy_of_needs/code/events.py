from onesim.events import Event
from typing import Any, List
from datetime import datetime

class SocialNeedsSatisfiedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        agent_id: str = "",
        social_interactions: List[Any] = [],
        satisfaction_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.agent_id = agent_id
        self.social_interactions = social_interactions
        self.satisfaction_level = satisfaction_level

class FeedbackProcessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        feedback_id: str = "",
        completion_status: str = "pending",
        results: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback_id = feedback_id
        self.completion_status = completion_status
        self.results = results

class PhysiologicalNeedsMetEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        agent_id: str = "",
        resources_provided: List[Any] = [],
        satisfaction_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.agent_id = agent_id
        self.resources_provided = resources_provided
        self.satisfaction_level = satisfaction_level

class SelfActualizationAchievedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        agent_id: str = "",
        goals_achieved: List[Any] = [],
        satisfaction_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.agent_id = agent_id
        self.goals_achieved = goals_achieved
        self.satisfaction_level = satisfaction_level

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)