from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class VoterSelectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: str = "",
        pollster_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.pollster_id = pollster_id

class OpinionRecordedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        pollster_id: str = "",
        opinion_data: object = None,
        completion_status: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.pollster_id = pollster_id
        self.opinion_data = opinion_data if opinion_data is not None else {}
        self.completion_status = completion_status

class ExpressOpinionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: str = "",
        policy_preferences: object = None,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.policy_preferences = policy_preferences if policy_preferences is not None else {}

class PreferencesAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: str = "",
        adjusted_preferences: object = None,
        interaction_trust_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.adjusted_preferences = adjusted_preferences if adjusted_preferences is not None else {}
        self.interaction_trust_level = interaction_trust_level