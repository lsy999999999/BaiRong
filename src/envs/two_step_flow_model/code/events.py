from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)


class InformationGeneratedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        information_content: str = "",
        target_opinion_leaders: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.information_content = information_content
        self.target_opinion_leaders = target_opinion_leaders


class InformationModifiedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        original_information: str = "",
        modified_information: str = "",
        opinion_leader_id: str = "",
        target_public_agents: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.original_information = original_information
        self.modified_information = modified_information
        self.opinion_leader_id = opinion_leader_id
        self.target_public_agents = target_public_agents


class InformationReceivedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        received_information: str = "",
        public_agent_reaction: str = "",
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.received_information = received_information
        self.public_agent_reaction = public_agent_reaction
        self.completion_status = completion_status