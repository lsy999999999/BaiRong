from onesim.events import Event
from typing import Any

class HealthDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = -1,
        service_requested: str = "none",
        priority_level: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.service_requested = service_requested
        self.priority_level = priority_level


class FamilyHealthImpactEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        family_id: int = -1,
        impact_type: str = "unknown",
        resource_change: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.family_id = family_id
        self.impact_type = impact_type
        self.resource_change = resource_change


class CommunityResourceEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        community_id: int = -1,
        resource_needs: str = "none",
        urgency_level: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.community_id = community_id
        self.resource_needs = resource_needs
        self.urgency_level = urgency_level


class PolicyImplementationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        policy_id: int = -1,
        affected_region: str = "unknown",
        resource_allocation_change: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.policy_id = policy_id
        self.affected_region = affected_region
        self.resource_allocation_change = resource_allocation_change


class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)


class HealthcareResourceAllocationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        allocation_status: str = "pending",
        allocated_resources: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.allocation_status = allocation_status
        self.allocated_resources = allocated_resources


class HealthcareServiceProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        service_status: str = "pending",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.service_status = service_status