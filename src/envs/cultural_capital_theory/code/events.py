from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class CulturalCapitalEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        cultural_capital_level: float = 0.0,
        education_decision: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.cultural_capital_level = cultural_capital_level
        self.education_decision = education_decision

class EducationCompletedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        education_level: str = 'None',
        job_search_status: str = 'not_started',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.education_level = education_level
        self.job_search_status = job_search_status

class JobOpportunityFoundEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        job_position: str = 'None',
        workflow_completion_status: str = 'incomplete',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.job_position = job_position
        self.workflow_completion_status = workflow_completion_status

class SocialClassAssessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        social_class: str = 'unknown',
        influence_on_cultural_capital: str = 'neutral',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.social_class = social_class
        self.influence_on_cultural_capital = influence_on_cultural_capital