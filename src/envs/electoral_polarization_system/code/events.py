from onesim.events import Event
from typing import Dict, List, Any

class StartEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class AgendaSetEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 agenda_topics: List[str] = None,
                 framing_strategy: str = "",
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.agenda_topics = agenda_topics if agenda_topics is not None else []
        self.framing_strategy = framing_strategy

class PolicyPositionedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 policy_positions: Dict[str, Any] = None,
                 target_voter_demographics: List[str] = None,
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.policy_positions = policy_positions if policy_positions is not None else {}
        self.target_voter_demographics = target_voter_demographics if target_voter_demographics is not None else []

class StrategyAdaptedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 feedback_data: Dict[str, Any] = None,
                 new_strategy: str = "",
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback_data = feedback_data if feedback_data is not None else {}
        self.new_strategy = new_strategy

class MediaInfluencedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 influence_strategy: str = "",
                 target_media_outlets: List[str] = None,
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.influence_strategy = influence_strategy
        self.target_media_outlets = target_media_outlets if target_media_outlets is not None else []

class MediaConsumedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 content_type: str = "",
                 attitude_change: float = 0.0,
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.content_type = content_type
        self.attitude_change = attitude_change

class CandidatesEvaluatedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 evaluation_criteria: List[str] = None,
                 evaluation_results: Dict[str, Any] = None,
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_criteria = evaluation_criteria if evaluation_criteria is not None else []
        self.evaluation_results = evaluation_results if evaluation_results is not None else {}

class AttitudesUpdatedEvent(Event):
    def __init__(self,
                 from_agent_id: str,
                 to_agent_id: str,
                 updated_attitudes: Dict[str, Any] = None,
                 influence_factors: List[str] = None,
                 **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.updated_attitudes = updated_attitudes if updated_attitudes is not None else {}
        self.influence_factors = influence_factors if influence_factors is not None else []