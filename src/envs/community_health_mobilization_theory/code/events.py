from onesim.events import Event
from typing import Any, List
from datetime import datetime

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class MobilizationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        activity_details: str = 'None',
        leader_id: str = 'unknown',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.activity_details = activity_details
        self.leader_id = leader_id

class BehaviorChangeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        influencing_member_id: str = 'unknown',
        influenced_member_id: str = 'unknown',
        behavior_change: str = 'None',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.influencing_member_id = influencing_member_id
        self.influenced_member_id = influenced_member_id
        self.behavior_change = behavior_change

class MobilizationCompletedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        completion_status: str = 'success',
        summary: str = 'None',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.completion_status = completion_status
        self.summary = summary

class PeerInfluenceEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        peer_id: str = 'unknown',
        target_member_id: str = 'unknown',
        influence_type: str = 'None',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.peer_id = peer_id
        self.target_member_id = target_member_id
        self.influence_type = influence_type

class GuidanceEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        guidance_details: str = 'None',
        expert_id: str = 'unknown',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.guidance_details = guidance_details
        self.expert_id = expert_id

class GuidanceCompletedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        completion_status: str = 'completed',
        results_summary: str = 'None',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.completion_status = completion_status
        self.results_summary = results_summary