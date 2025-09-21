from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class BehaviorTendenciesInitializedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = 0,
        behavior_tendencies: List = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.behavior_tendencies = behavior_tendencies

class AssignedToGroupEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = 0,
        group_id: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.group_id = group_id

class InteractionObservedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        observer_id: int = 0,
        interaction_details: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.observer_id = observer_id
        self.interaction_details = interaction_details

class BehaviorAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = 0,
        adjusted_behavior_tendencies: List = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.adjusted_behavior_tendencies = adjusted_behavior_tendencies

class MemberAddedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        group_id: int = 0,
        individual_id: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.group_id = group_id
        self.individual_id = individual_id

class GroupNormsUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        group_id: int = 0,
        updated_norms: List = [],
        status: str = 'success',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.group_id = group_id
        self.updated_norms = updated_norms
        self.status = status