from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ParticipationDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: str = 'unknown',
        participation_decision: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.participation_decision = participation_decision

class NonParticipationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: str = 'unknown',
        reason_for_non_participation: str = 'none',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.reason_for_non_participation = reason_for_non_participation

class CandidateSelectionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: str = 'unknown',
        selected_candidate_id: str = 'none',
        preference_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.selected_candidate_id = selected_candidate_id
        self.preference_score = preference_score